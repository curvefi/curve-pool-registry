import itertools as it
from collections import Counter, defaultdict
from enum import IntEnum
from typing import List, Tuple


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
        # coin register count - if count < 0 then it doesn't exist
        self._coin_register_counter = Counter()
        # number of unique coins registered
        self.coin_count = 0
        # unique coins registered
        self.get_coin = set()
        # coin_a -> coin_b -> # of time registered
        self._coin_swap_register = defaultdict(Counter)
        # coin -> # of unique coins available to swap with
        self.get_coin_swap_count = Counter()
        # unique set of coins (coin_b) which can swap against coin_a
        self.get_coin_swap_complement = defaultdict(set)
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

    def _register_coins(self, coins: List[str]):
        self._coin_register_counter.update(coins)
        self.get_coin = set((+self._coin_register_counter).keys())
        self.coin_count = len(self.get_coin)

    def _register_coin_pairs(self, pairings: List[Tuple[str, str]]):
        coins = set()
        for coin_a, coin_b in pairings:
            coins.update([coin_a, coin_b])
            self._coin_swap_register[coin_a].update([coin_b])
            self._coin_swap_register[coin_b].update([coin_a])

        for coin in coins:
            self.get_coin_swap_complement[coin] = set((+self._coin_swap_register[coin]).keys())
            self.get_coin_swap_count[coin] = len(self.get_coin_swap_complement[coin])

    def _unregister_coins(self, coins: List[str]):
        self._coin_register_counter.subtract(coins)
        self.get_coin = set((+self._coin_register_counter).keys())
        self.coin_count = len(self.get_coin)

    def _unregister_coin_pairs(self, pairings: List[Tuple[str, str]]):
        coins = set()
        for coin_a, coin_b in pairings:
            coins.update([coin_a, coin_b])
            self._coin_swap_register[coin_a].subtract([coin_b])
            self._coin_swap_register[coin_b].subtract([coin_a])

        for coin in coins:
            self.get_coin_swap_complement[coin] = set((+self._coin_swap_register[coin]).keys())
            self.get_coin_swap_count[coin] = len(self.get_coin_swap_complement[coin])

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

        # register coins
        self._register_coins(it.chain(wrapped_coins, underlying_coins))

        # register coin pairs
        wrapped_pairs = it.combinations(wrapped_coins, 2)
        underlying_pairs = it.combinations(underlying_coins, 2)
        self._register_coin_pairs(it.chain(wrapped_pairs, underlying_pairs))

        # update timestamp
        self.last_updated = timestamp

    def add_pool_without_underlying(
        self, address: str, coins: List[str], lp_token: str, timestamp: int
    ):
        """Add base pool and update state."""
        # append pool to list of pools
        base_pool = Pool.base_pool(address, coins, lp_token)
        self.pools.append(base_pool)

        # register coins
        self._register_coins(coins)

        # register coin pairs
        coin_pairs = it.combinations(coins, 2)
        self._register_coin_pairs(coin_pairs)

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

        # register coins
        self._register_coins(meta_coins)

        # register coin pairs
        meta_pairs = it.combinations(meta_coins, 2)
        meta_base_pairs = ((m_coin, b_coin) for m_coin in meta_coins[:-1] for b_coin in base_coins)
        self._register_coin_pairs(it.chain(meta_pairs, meta_base_pairs))

        # update timestamp
        self.last_updated = timestamp

    def _remove_pool(self, pool: Pool, timestamp: int):
        """Remove pool and update state."""

        wrapped_coins = pool.coins
        underlying_coins = pool.underlying_coins

        # unregister coins
        self._unregister_coins(it.chain(wrapped_coins, underlying_coins))

        # unregister coin pairs
        wrapped_pairs = it.combinations(wrapped_coins, 2)
        underlying_pairs = it.combinations(underlying_coins, 2)
        self._unregister_coin_pairs(it.chain(wrapped_pairs, underlying_pairs))

        # update timestamp
        self.last_updated = timestamp

    def _remove_pool_without_underlying(self, pool: Pool, timestamp: int):
        """Remove pool and update state."""

        coins = pool.coins

        # unregister coins
        self._unregister_coins(coins)

        # unregister coin pairs
        coin_pairs = it.combinations(coins, 2)
        self._unregister_coin_pairs(coin_pairs)

        # update timestamp
        self.last_updated = timestamp

    def _remove_metapool(self, pool: Pool, timestamp: int):
        """Remove metapool and update state."""

        meta_coins = pool.coins
        base_coins = pool.base_coins

        # unregister coins
        self._unregister_coins(meta_coins)

        # unregister coin pairs
        meta_pairs = it.combinations(meta_coins, 2)
        meta_base_pairs = ((m_coin, b_coin) for m_coin in meta_coins[:-1] for b_coin in base_coins)
        self._unregister_coin_pairs(it.chain(meta_pairs, meta_base_pairs))

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
