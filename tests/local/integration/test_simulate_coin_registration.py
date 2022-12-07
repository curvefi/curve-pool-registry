"""Test the effect of adding and removing pools on coin registration.

With the new `swappable_coins` and `swap_coin_for` functions we now have the ability to
iterate through the coins registered in curve pools (base pools, lending pools, and meta pools).
We can also iterate through the pairings which users can swap a given coin (coin a) against
(coin b).

With the unit tests we have confirmed basic functionality of removing pools and adding them,
however to further verify the functionality this stateful test will continually add and subtract
pools, thereby verifying that functionality isn't lost as more pools are added/subtracted.
"""
from typing import List

from brownie.network.account import Account
from brownie.network.contract import Contract, ContractContainer
from brownie.network.state import Chain
from brownie.test import strategy
from coin_register_utils import Pool, PoolType, Registry

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


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
        return self.cERC20.deploy(name, symbol, decimals, erc20, 10**18, self.tx_params)

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

    st_sleep = strategy("uint256", max_value=86400)
    st_random = strategy("uint256", max_value=2**32)

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
            "",
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
            "",
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
        if len(self.state.base_pools) == 0:
            return

        # select a random base pool
        pool_index = st_random % len(self.state.base_pools)
        # base_pool
        base_pool: Pool = self.state.base_pools[pool_index]
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
            meta_pool, n_coins, lp_token, pack_values([18] * n_coins), "", self.tx_params
        )

        # update state
        self.state.add_metapool(
            meta_pool.address,
            list(map(str, meta_coins)),
            lp_token.address,
            base_pool.coins,
            tx.timestamp,
        )

    def rule_chain_sleep(self, st_sleep):
        self.chain.sleep(st_sleep)

    def rule_remove_pool(self, st_random):
        if len(self.state.pools) == 0:
            return
        # select a random pool
        random_index = st_random % len(self.state.pools)

        # verify our pool isn't the base of any meta_pools pools
        pool: Pool = self.state.pools[random_index]

        # if our pool is the base of a meta pool don't remove it
        if pool.pool_type == PoolType.BASE:
            for _pool in self.state.meta_pools:
                if pool.lp_token in _pool.coins:
                    return

        # remove from on chain registry
        tx = self.registry.remove_pool(pool.address)

        # update our state
        self.state.remove_pool(pool, tx.timestamp)
        self.state.pools.remove(pool)

    def invariant_coin_count(self):
        assert self.registry.coin_count() == self.state.coin_count

    def invariant_get_all_swappable_coins(self):
        registered_coins = {self.registry.get_coin(i) for i in range(self.state.coin_count)}

        assert registered_coins == self.state.get_coin

    def invariant_coin_swap_count(self):
        for coin in self.state.get_coin:
            assert self.registry.get_coin_swap_count(coin) == self.state.get_coin_swap_count[coin]

    def invariant_swap_coin_for(self):
        for coin, expected_coin_set in self.state.get_coin_swap_complement.items():
            coin_set = {
                self.registry.get_coin_swap_complement(coin, i)
                for i in range(self.state.get_coin_swap_count[coin])
            }
            assert coin_set == expected_coin_set

    def invariant_last_updated(self):
        assert self.state.last_updated == self.registry.last_updated()


def test_simulate_coin_registry(
    state_machine, registry, alice, chain, ERC20, cERC20, PoolMockV2, MetaPoolMock
):
    state_machine(
        StateMachine,
        registry,
        alice,
        chain,
        ERC20,
        cERC20,
        PoolMockV2,
        MetaPoolMock,
        # settings={"stateful_step_count": 25},
    )
