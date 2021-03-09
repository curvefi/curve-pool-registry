"""Test the effect of adding and removing pools on coin registration.

With the new `swappable_coins` and `swap_coin_for` functions we now have the ability to
iterate through the coins registered in curve pools (base pools, lending pools, and meta pools).
We can also iterate through the pairings which users can swap a given coin (coin a) against
(coin b).

With the unit tests we have confirmed basic functionality of removing pools and adding them,
however to further verify the functionality this stateful test will continually add and subtract
pools, thereby verifying that functionality isn't lost as more pools are added/subtracted.
"""
import itertools as it
from collections import Counter, defaultdict
from enum import IntEnum
from typing import List

from brownie.network.account import Account
from brownie.network.contract import Contract, ContractContainer
from brownie.network.state import Chain
from brownie.test import strategy

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class PoolType(IntEnum):

    BASE = 0
    LENDING = 1
    META = 2


class Pool:
    def __init__(
        self,
        address: str,
        coins: List[str],
        lp_token: str,
        underlying_coins: List[str] = None,
        base_coins: List[str] = None,
        pool_type: PoolType = PoolType.BASE,
    ):
        self.address = address
        self.coins = coins
        self.lp_token = lp_token
        self.underlying_coins = underlying_coins
        self.base_coins = base_coins
        self.pool_type = pool_type

    @classmethod
    def base_pool(cls, address: str, coins: List[str], lp_token: str):
        return cls(address, coins, lp_token)

    @classmethod
    def lending_pool(
        cls, address: str, coins: List[str], lp_token: str, underlying_coins: List[str]
    ):
        return cls(address, coins, lp_token, underlying_coins, pool_type=PoolType.LENDING)

    @classmethod
    def meta_pool(cls, address: str, coins: List[str], lp_token: str, base_coins: List[str]):
        return cls(address, coins, lp_token, base_coins=base_coins, pool_type=PoolType.META)


class Registry:
    """A Registry instance state emulator."""

    def __init__(self):
        # number of unique coins registered
        self.coin_count = 0
        # coin registration count
        self._coin_register_counter = Counter()
        # unique coins registered, if count < 0 then it doesn't exist
        self.get_swappable_coin = set()
        # coin -> # of unique coins available to swap with
        self.coin_swap_count = Counter()
        # coin_a -> coin_b -> # of time registered
        self._coin_swap_register = defaultdict(Counter)
        # unique set of coins (coin_b) which can swap against coin_a
        self.swap_coin_for = defaultdict(set)
        # timestamp of last update
        self.last_updated = 0

        # available pools with their type
        self.pools = []

    @property
    def base_pools(self):
        return [pool for pool in self.pools if pool.pool_type == PoolType.BASE]

    @property
    def lending_pools(self):
        return [pool for pool in self.pools if pool.pool_type == PoolType.LENDING]

    @property
    def meta_pools(self):
        return [pool for pool in self.pools if pool.pool_type == PoolType.META]

    def add_pool_without_underlying(
        self, address: str, coins: List[str], lp_token: str, timestamp: int
    ):
        """Add base pool and update state."""
        # append pool to list of pools
        base_pool = Pool.base_pool(address, coins, lp_token)
        self.pools.append(base_pool)

        # update coin counter
        self._coin_register_counter.update(coins)
        # update count of unique coins
        self.coin_count = len(+self._coin_register_counter)  # unary addition removes <= 0 counts
        # update set of registered coins
        self.get_swappable_coin.update(coins)
        # for each pairing update amount of unique coins to swap for and the count for each pair
        pairings = it.combinations(coins, 2)
        for coin_a, coin_b in pairings:
            # update unique set of counter coins to swap against
            self.swap_coin_for[coin_a].add(coin_b)
            self.swap_coin_for[coin_b].add(coin_a)

            # update register counts
            self._coin_swap_register[coin_a].update([coin_b])
            self._coin_swap_register[coin_b].update([coin_a])

        # update the count of unique coins available to swap coin_a against
        self.coin_swap_count = Counter(
            {coin: len(coin_set) for coin, coin_set in self.swap_coin_for.items()}
        )

        # update timestamp
        self.last_updated = timestamp

    def add_pool(
        self,
        address: str,
        wrapped_coins: List[str],
        underlying_coins: List[str],
        lp_token: str,
        timestamp: int,
    ):
        """Add lending pool and update state."""
        # append pool to list of pools
        lending_pool = Pool.lending_pool(address, wrapped_coins, lp_token, underlying_coins)
        self.pools.append(lending_pool)

        # update coin counter
        self._coin_register_counter.update(wrapped_coins)
        self._coin_register_counter.update(underlying_coins)
        # update count of unique coins
        self.coin_count = len(+self._coin_register_counter)  # unary addition removes <= 0 counts
        # update set of registered coins
        self.get_swappable_coin.update(wrapped_coins)
        self.get_swappable_coin.update(underlying_coins)
        # for each pairing update amount of unique coins to swap for and the count for each pair
        pairings = it.combinations(wrapped_coins, 2)
        for coin_a, coin_b in pairings:
            # update unique set of counter coins to swap against
            self.swap_coin_for[coin_a].add(coin_b)
            self.swap_coin_for[coin_b].add(coin_a)

            # update register counts
            self._coin_swap_register[coin_a].update([coin_b])
            self._coin_swap_register[coin_b].update([coin_a])

        pairings = it.combinations(underlying_coins, 2)
        for coin_a, coin_b in pairings:
            # update unique set of counter coins to swap against
            self.swap_coin_for[coin_a].add(coin_b)
            self.swap_coin_for[coin_b].add(coin_a)

            # update register counts
            self._coin_swap_register[coin_a].update([coin_b])
            self._coin_swap_register[coin_b].update([coin_a])

        # update the count of unique coins available to swap coin_a against
        self.coin_swap_count = Counter(
            {coin: len(coin_set) for coin, coin_set in self.swap_coin_for.items()}
        )

        # update timestamp
        self.last_updated = timestamp

    def add_metapool(
        self,
        address: str,
        meta_coins: List[str],
        lp_token: str,
        base_coins: List[str],
        timestamp: int,
    ):
        """Add metapool and update state."""
        # append pool to list of pools
        meta_pool = Pool.meta_pool(address, meta_coins, lp_token, base_coins)
        self.pools.append(meta_pool)

        # update coin counter
        self._coin_register_counter.update(meta_coins)
        # update count of unique coins
        self.coin_count = len(+self._coin_register_counter)  # unary addition removes <= 0 counts
        # update set of registered coins
        self.get_swappable_coin.update(meta_coins)
        # for each pairing update amount of unique coins to swap for and the count for each pair
        pairings = it.combinations(meta_coins, 2)
        for coin_a, coin_b in pairings:
            # update unique set of counter coins to swap against
            self.swap_coin_for[coin_a].add(coin_b)
            self.swap_coin_for[coin_b].add(coin_a)

            # update register counts
            self._coin_swap_register[coin_a].update([coin_b])
            self._coin_swap_register[coin_b].update([coin_a])

        pairings = (
            (meta_coin, base_coin) for meta_coin in meta_coins[:-1] for base_coin in base_coins
        )
        for coin_a, coin_b in pairings:
            # update unique set of counter coins to swap against
            self.swap_coin_for[coin_a].add(coin_b)
            self.swap_coin_for[coin_b].add(coin_a)

            # update register counts
            self._coin_swap_register[coin_a].update([coin_b])
            self._coin_swap_register[coin_b].update([coin_a])

        # update the count of unique coins available to swap coin_a against
        self.coin_swap_count = Counter(
            {coin: len(coin_set) for coin, coin_set in self.swap_coin_for.items()}
        )

        # update timestamp
        self.last_updated = timestamp

    def _remove_pool_without_underlying(self, pool: Pool, timestamp: int):
        """Remove pool and update state."""

        coins = pool.coins

        # update the register counts by subtracting the amount of times a coin is registered
        self._coin_register_counter.subtract(coins)
        # update count of unique coins
        self.coin_count = len(+self._coin_register_counter)  # unary addition removes <= 0 counts
        # update set of registered coins
        self.get_swappable_coin = set((+self._coin_register_counter).keys())

        # now we need to remove the pairings, so first we will track how many times
        # each coin is paired with another coin
        pairings = it.combinations(coins, 2)
        remove_counts = defaultdict(Counter)

        # for each of the pairs update our local removal counter
        for coin_a, coin_b in pairings:
            # update our counts for each coin
            remove_counts[coin_a].update([coin_b])
            remove_counts[coin_b].update([coin_a])

        # now we update our swap register, by removing the appropriate amount of
        # swaps available for each coin with each of it's counter parts
        for coin, counter in remove_counts.items():
            self._coin_swap_register[coin].subtract(counter)

        # update out swap_coin_for set, in this case we use our register
        # which keeps track of how many times a swap pair has been registered
        # if the pairing is no longer registered it obviously shouldn't be included.
        # Note: the unary addition on a counter, only keeps values with a positive value
        for coin in self.swap_coin_for:
            self.swap_coin_for[coin] = set((+self._coin_swap_register[coin]).keys())

        # lastly we update our count of unique coins we can swap against
        # using the swap_coin_for dictionary.
        self.coin_swap_count = Counter(
            {coin: len(coin_set) for coin, coin_set in self.swap_coin_for.items()}
        )

        # update timestamp
        self.last_updated = timestamp

    def _remove_pool(self, pool: Pool, timestamp: int):
        """Remove pool and update state."""

        wrapped_coins = pool.coins
        underlying_coins = pool.underlying_coins

        # update the register counts by subtracting the amount of times a coin is registered
        self._coin_register_counter.subtract(wrapped_coins)
        self._coin_register_counter.subtract(underlying_coins)
        # update count of unique coins
        self.coin_count = len(+self._coin_register_counter)  # unary addition removes <= 0 counts
        # update set of registered coins
        self.get_swappable_coin = set((+self._coin_register_counter).keys())

        for coins in (wrapped_coins, underlying_coins):
            # now we need to remove the pairings, so first we will track how many times
            # each coin is paired with another coin
            pairings = it.combinations(coins, 2)
            remove_counts = defaultdict(Counter)

            # for each of the pairs update our local removal counter
            for coin_a, coin_b in pairings:
                # update our counts for each coin
                remove_counts[coin_a].update([coin_b])
                remove_counts[coin_b].update([coin_a])

            # now we update our swap register, by removing the appropriate amount of
            # swaps available for each coin with each of it's counter parts
            for coin, counter in remove_counts.items():
                self._coin_swap_register[coin].subtract(counter)

        # update out swap_coin_for set, in this case we use our register
        # which keeps track of how many times a swap pair has been registered
        # if the pairing is no longer registered it obviously shouldn't be included.
        # Note: the unary addition on a counter, only keeps values with a positive value
        for coin in self.swap_coin_for:
            self.swap_coin_for[coin] = set((+self._coin_swap_register[coin]).keys())

        # lastly we update our count of unique coins we can swap against
        # using the swap_coin_for dictionary.
        self.coin_swap_count = Counter(
            {coin: len(coin_set) for coin, coin_set in self.swap_coin_for.items()}
        )

        # update timestamp
        self.last_updated = timestamp

    def _remove_metapool(self, pool: Pool, timestamp: int):
        """Remove metapool and update state."""

        meta_coins = pool.coins
        base_coins = pool.base_coins

        # update the register counts by subtracting the amount of times a coin is registered
        self._coin_register_counter.subtract(meta_coins)
        # update count of unique coins
        self.coin_count = len(+self._coin_register_counter)  # unary addition removes <= 0 counts
        # update set of registered coins
        self.get_swappable_coin = set((+self._coin_register_counter).keys())

        for i in [True, False]:
            # now we need to remove the pairings, so first we will track how many times
            # each coin is paired with another coin
            if i:
                pairings = it.combinations(meta_coins, 2)
            else:
                pairings = (
                    (meta_coin, base_coin)
                    for meta_coin in meta_coins[:-1]
                    for base_coin in base_coins
                )
            remove_counts = defaultdict(Counter)

            # for each of the pairs update our local removal counter
            for coin_a, coin_b in pairings:
                # update our counts for each coin
                remove_counts[coin_a].update([coin_b])
                remove_counts[coin_b].update([coin_a])

            # now we update our swap register, by removing the appropriate amount of
            # swaps available for each coin with each of it's counter parts
            for coin, counter in remove_counts.items():
                self._coin_swap_register[coin].subtract(counter)

        # update out swap_coin_for set, in this case we use our register
        # which keeps track of how many times a swap pair has been registered
        # if the pairing is no longer registered it obviously shouldn't be included.
        # Note: the unary addition on a counter, only keeps values with a positive value
        for coin in self.swap_coin_for:
            self.swap_coin_for[coin] = set((+self._coin_swap_register[coin]).keys())

        # lastly we update our count of unique coins we can swap against
        # using the swap_coin_for dictionary.
        self.coin_swap_count = Counter(
            {coin: len(coin_set) for coin, coin_set in self.swap_coin_for.items()}
        )

        # update timestamp
        self.last_updated = timestamp

    def remove_pool(self, pool: Pool, timestamp: int):
        """Remove a pool and update state."""
        if pool.pool_type == PoolType.BASE:
            self._remove_pool_without_underlying(pool, timestamp)
        elif pool.pool_type == PoolType.LENDING:
            self._remove_pool(pool, timestamp)
        else:
            self._remove_metapool(pool, timestamp)


class BaseHelper:
    def __init__(
        cls,
        alice: Account,
        chain: Chain,
        ERC20: ContractContainer,
        cERC20: ContractContainer,
        PoolMockV2: ContractContainer,
        MetaPoolMock: ContractContainer,
    ):
        cls.alice = alice
        cls.chain = chain
        cls.ERC20 = ERC20
        cls.cERC20 = cERC20
        cls.PoolMockV2 = PoolMockV2
        cls.MetaPoolMock = MetaPoolMock

        cls.tx_params = {"from": alice}

    def _deploy_erc20(
        self, name: str = "Test Token", symbol: str = "TST", decimals: int = 18
    ) -> Contract:
        """Deploy an ERC20 instance."""
        count = len(self.ERC20)
        name, symbol = f"{name} {count}", f"{symbol} {count}"
        return self.ERC20.deploy(name, symbol, decimals, self.tx_params)

    def _batch_deploy_erc20(self, amount: int = 3) -> List[Contract]:
        """Deploy more than one token at once using defaults."""
        return [self._deploy_erc20() for _ in range(amount)]

    def _deploy_wrapped_erc20(self, erc20: Contract) -> Contract:
        """Deploy an instance of a wrapped coin."""
        count = len(self.cERC20)
        name, symbol, decimals = f"Wrapped Token {count}", f"wTST {count}", 18
        return self.cERC20.deploy(name, symbol, decimals, erc20, 10 ** 18, self.tx_params)

    def _batch_deploy_wrapped_erc20(self, erc20s: List[Contract]) -> List[Contract]:
        """Batch deploy a set of wrapped ERC20 contracts."""
        return [self._deploy_wrapped_erc20(erc20) for erc20 in erc20s]

    def _deploy_base_pool(self, coins: List[Contract]) -> Contract:
        """Deploy a base pool (no underlying coins)."""
        n_coins = len(coins)
        coins = coins + [ZERO_ADDRESS] * (4 - n_coins)

        return self.PoolMockV2.deploy(
            n_coins, coins, [ZERO_ADDRESS] * 4, 70, 4000000, self.tx_params
        )

    def _deploy_lending_pool(
        self, coins: List[Contract], underlying_coins: List[Contract]
    ) -> Contract:
        """Deploy a lending pool with wrapped and underlying coins."""
        n_coins = len(underlying_coins)
        coins = coins + [ZERO_ADDRESS] * (4 - len(coins))
        underlying_coins = underlying_coins + [ZERO_ADDRESS] * (4 - n_coins)

        return self.PoolMockV2.deploy(n_coins, coins, underlying_coins, 70, 4000000, self.tx_params)

    def _deploy_meta_pool(
        self, meta_coins: List[Contract], underlying_coins: List[Contract], base_pool: Contract
    ) -> Contract:
        """Deploy a meta pool, with a base pool (underlying coins are coins in base)."""
        n_metacoins = len(meta_coins)
        n_coins = len(underlying_coins)

        meta_coins = meta_coins + [ZERO_ADDRESS] * (4 - n_metacoins)
        underlying_coins = underlying_coins + [ZERO_ADDRESS] * (4 - n_coins)

        return self.MetaPoolMock.deploy(
            n_metacoins,
            n_coins,
            base_pool,
            meta_coins,
            underlying_coins,
            70,
            4000000,
            self.tx_params,
        )


class StateMachine(BaseHelper):

    st_random = strategy("uint256")

    def __init__(cls, registry: Contract, *args, **kwargs):
        super().__init__(cls, *args, **kwargs)

        cls.registry = registry

    def setup(self):
        self.state = Registry()

    def rule_add_pool_without_underlying(self):
        # deploy 3 coins
        coins = self._batch_deploy_erc20()
        # number of coins
        n_coins = len(coins)
        # deploy the base pool
        base_pool = self._deploy_base_pool(coins)
        # make an lp token
        lp_token = self._deploy_erc20()

        # add the pool on chain
        tx = self.registry.add_pool_without_underlying(
            base_pool,  # the swap, but I call it a pool
            n_coins,
            lp_token,
            "0x00",
            pack_values([18] * n_coins),
            0,
            hasattr(base_pool, "initial_A"),
            False,  # is_v1
            self.tx_params,
        )

        # update our state
        self.state.add_pool_without_underlying(
            base_pool.address, list(map(str, coins)), lp_token.address, tx.timestamp
        )

    def rule_add_pool(self):
        # deploy 3 coins
        underlying_coins = self._batch_deploy_erc20()
        # deploy wrapped coins
        wrapped_coins = self._batch_deploy_wrapped_erc20(underlying_coins)
        # coin amount
        n_coins = len(wrapped_coins)
        # deploy pool/swap
        lending_pool = self._deploy_lending_pool(wrapped_coins, underlying_coins)
        # lp token
        lp_token = self._deploy_erc20()
        # rate method id
        rate_method_id = self.cERC20.signatures["exchangeRateStored"]

        # add the pool on chain
        tx = self.registry.add_pool(
            lending_pool,
            n_coins,
            lp_token,
            rate_method_id,
            pack_values([18] * n_coins),
            pack_values([18] * n_coins),
            hasattr(lending_pool, "initial_A"),
            False,
            self.tx_params,
        )

        # update state
        self.state.add_pool(
            lending_pool.address,
            list(map(str, wrapped_coins)),
            list(map(str, underlying_coins)),
            lp_token.address,
            tx.timestamp,
        )

    def rule_add_metapool(self, st_random):
        if len(self.state.pools) == 0:
            return

        # select a random base pool
        pool_index = st_random % len(self.state.pools)
        # base_pool
        base_pool: Pool = self.state.pools[pool_index]
        # deploy our coins
        meta_coins = self._batch_deploy_erc20() + [base_pool.lp_token]
        # number of coins
        n_coins = len(meta_coins)

        # deploy meta_pool
        meta_pool = self._deploy_meta_pool(meta_coins, base_pool.coins, base_pool.address)
        # lp token
        lp_token = self._deploy_erc20()

        # add the pool on chain
        tx = self.registry.add_metapool(
            meta_pool, n_coins, lp_token, pack_values([18] * n_coins), self.tx_params
        )

        # update state
        self.state.add_metapool(
            meta_pool.address,
            list(map(str, meta_coins)),
            lp_token.address,
            base_pool.coins,
            tx.timestamp,
        )

    def rule_chain_sleep(self, st_random):
        DAY = 60 * 60 * 24
        self.chain.sleep(st_random % DAY)

    def rule_remove_pool(self, st_random):
        if len(self.state.pools) == 0:
            return
        # select a random pool
        random_index = st_random % len(self.state.pools)

        # verify our pool isn't the base of any meta_pools pools
        pool = self.state.pools[random_index]
        is_base = True
        while is_base:
            for meta_pool in self.state.meta_pools:
                meta_pool: Pool = meta_pool
                if pool.lp_token in meta_pool.coins:
                    # make this meta_pool our new pool
                    pool = meta_pool
                    break
            else:  # only run if the loop completes without finding anything
                is_base = False

        pool_index = self.state.pools.index(pool)
        pool: Pool = self.state.pools.pop(pool_index)  # remove the pool from our pool list

        # remove from on chain registry
        tx = self.registry.remove_pool(pool.address)

        # update our state
        self.state.remove_pool(pool, tx.timestamp)

    def invariant_coin_count(self):
        assert self.registry.coin_count() == self.state.coin_count

    def invariant_get_all_swappable_coins(self):
        registered_coins = {
            self.registry.get_swappable_coin(i) for i in range(self.state.coin_count)
        }

        assert registered_coins == self.state.get_swappable_coin

    def invariant_coin_swap_count(self):
        counter = {
            coin: self.registry.coin_swap_count(coin) for coin in self.state.get_swappable_coin
        }

        assert Counter(counter) == +self.state.coin_swap_count

    def invariant_swap_coin_for(self):
        coin_sets = {
            coin: {self.registry.swap_coin_for(coin, i) for i in range(count)}
            for coin, count in self.state.coin_swap_count.items()
        }

        for coin, coin_set in coin_sets.items():
            assert coin_set == self.state.swap_coin_for[coin]

    def invariant_last_updated(self):
        assert (
            self.state.last_updated - 1 <= self.registry.last_updated() <= self.state.last_updated
        )


def test_simulate_coin_registry(
    state_machine, registry, alice, chain, ERC20, cERC20, PoolMockV2, MetaPoolMock
):
    state_machine(StateMachine, registry, alice, chain, ERC20, cERC20, PoolMockV2, MetaPoolMock)
