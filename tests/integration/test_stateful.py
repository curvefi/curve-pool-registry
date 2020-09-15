import brownie
from brownie.test import contract_strategy, strategy

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

from scripts.utils import pack_values


class StateMachine:

    # stateful test information
    pool_info = {}
    added_pools = set()

    # state machine rules
    st_pool = contract_strategy("PoolMock")
    st_coin = contract_strategy("yERC20")
    st_coin2 = contract_strategy("yERC20")
    st_underlying = contract_strategy("ERC20")
    st_underlying2 = contract_strategy("ERC20")
    st_decimals = strategy('uint8[8]', min_value=1, max_value=42)
    st_amount = strategy('uint256', max_value=1e18)

    def __init__(cls, PoolMock, accounts, registry, coins, underlying, USDT):
        """
        Initial state machine setup.

        This method only runs once, prior to the initial snapshot.
        """
        cls.accounts = accounts
        cls.registry = registry

         # fund test account with initial balances
        for coin in coins + underlying:
            coin._mint_for_testing(1e18, {'from': accounts[0]})
            coin.approve(registry, 2**256-1, {'from': accounts[0]})

        # create pools
        for i in range(3):
            cls._create_pool(PoolMock, 2, coins[:2], underlying[:2], USDT)
            coins.insert(0, coins.pop())
            underlying.insert(0, underlying.pop())

        for i in range(2):
            cls._create_pool(PoolMock, 3, coins[:3], underlying[:3], USDT)
            coins.insert(0, coins.pop())
            underlying.insert(0, underlying.pop())

        cls._create_pool(PoolMock, 4, coins, underlying, USDT)

    @classmethod
    def _create_pool(cls, PoolMock, n_coins, coins, underlying, USDT):
        # Create a pool and add it to `cls.pool_info`
        coins = coins + ([ZERO_ADDRESS] * (8-n_coins))
        underlying = underlying + ([ZERO_ADDRESS] * (8-n_coins))

        pool = PoolMock.deploy(
            n_coins,
            coins[:4],
            underlying[:4],
            70,
            4000000,
            {'from': cls.accounts[0]}
        )
        cls.pool_info[pool] = {'coins': coins, 'underlying': underlying}

    def setup(self):
        """
        Reset test conditions between each run.
        """
        self.added_pools.clear()

    def rule_add_pool(self, st_pool, st_decimals):
        """
        Attempt to add a pool to the registry.

        Decimal values are randomized with `st_decimals` - this has no effect on
        other rules, and helps to verify `Registry.get_pool_coins`

        Revert Paths
        ------------
        * The pool has already been added
        """
        n_coins = st_pool.n_coins()

        if st_pool in self.added_pools:
            with brownie.reverts("dev: pool exists"):
                self.registry.add_pool(
                    st_pool,
                    n_coins,
                    ZERO_ADDRESS,
                    ZERO_ADDRESS,
                    "0x00",
                    "0x00",
                    "0x00",
                    True,
                    True,
                    {'from': self.accounts[0]}
                )
        else:
            decimals = st_decimals[:n_coins] + [0] * (8 - n_coins)
            udecimals = st_decimals[-n_coins:] + [0] * (8 - n_coins)

            self.registry.add_pool(
                st_pool,
                n_coins,
                ZERO_ADDRESS,
                ZERO_ADDRESS,
                "0x00",
                pack_values(decimals),
                pack_values(udecimals),
                True,
                True,
                {'from': self.accounts[0]}
            )
            self.added_pools.add(st_pool)
            self.pool_info[st_pool]['decimals'] = decimals
            self.pool_info[st_pool]['underlying_decimals'] = udecimals

    def rule_remove_pool(self, st_pool):
        """
        Attempt to remove a pool from the registry.

        Revert Paths
        ------------
        * The pool has not been added, or was already removed
        """
        if st_pool in self.added_pools:
            self.registry.remove_pool(st_pool, {'from': self.accounts[0]})
            self.added_pools.discard(st_pool)
        else:
            with brownie.reverts("dev: pool does not exist"):
                self.registry.remove_pool(st_pool, {'from': self.accounts[0]})

    def _exchange(self, pool, coin, coin2, amount):
        # attempt to perform an exchange
        if pool in self.added_pools and coin != coin2:
            from_balance = coin.balanceOf(self.accounts[0])
            to_balance = coin2.balanceOf(self.accounts[0])

            if amount <= from_balance:
                expected = self.registry.get_exchange_amount(pool, coin, coin2, amount)
                self.registry.exchange(pool, coin, coin2, amount, 0)
                assert coin.balanceOf(self.accounts[0]) == from_balance - amount
                assert coin2.balanceOf(self.accounts[0]) == to_balance + expected
            else:
                with brownie.reverts():
                    self.registry.exchange(pool, coin, coin2, amount, 0)

        else:
            with brownie.reverts():
                self.registry.exchange(pool, coin, coin2, amount, 0)


    def rule_exchange(self, st_coin, st_coin2, st_amount):
        """
        Attempt to perform a token exchange.

        The exchange is attempted with the first pool in `cls.pool_info` that
        provides a market for `st_coin` and `st_coin2`.

        Revert Paths
        ------------
        * The pool has not been added
        * `st_coin` and `st_coin2` are the same coin
        * `accounts[0]` has an insufficient balance of `st_coin`
        """
        pool = next(
            k for k, v in self.pool_info.items() if
            st_coin in v['coins'] and
            st_coin2 in v['coins']
        )
        self._exchange(pool, st_coin, st_coin2, st_amount)

    def rule_exchange_underlying(self, st_underlying, st_underlying2, st_amount):
        """
        Attempt to perform a token exchange with underlying tokens.

        The exchange is attempted with the first pool in `cls.pool_info` that
        provides a market for `st_underlying` and `st_underlying2`.

        Revert Paths
        ------------
        * The pool has not been added
        * `st_underlying` and `st_underlying` are the same coin
        * `accounts[0]` has an insufficient balance of `st_underlying`
        """
        pool = next(
            k for k, v in self.pool_info.items() if
            st_underlying in v['underlying'] and
            st_underlying2 in v['underlying']
        )
        self._exchange(pool, st_underlying, st_underlying2, st_amount)

    def invariant_coins(self):
        """
        Invariant for `get_pool_coins`

        Checks
        ------
        * Added pools should return the correct coins, underlying coins, and decimals
        * Pools that were not added, or were removed, should return zero values
        """
        for pool in self.pool_info:
            coins = self.registry.get_pool_coins(pool)
            if pool in self.added_pools:
                coins = self.registry.get_pool_coins(pool)
                assert coins['coins'] == self.pool_info[pool]['coins']
                assert coins['underlying_coins'] == self.pool_info[pool]['underlying']
                assert coins['decimals'] == self.pool_info[pool]['decimals']
                assert coins['underlying_decimals'] == self.pool_info[pool]['underlying_decimals']
            else:
                assert coins['coins'] == [ZERO_ADDRESS] * 8
                assert coins['underlying_coins'] == [ZERO_ADDRESS] * 8
                assert coins['decimals'] == [0] * 8
                assert coins['underlying_decimals'] == [0] * 8


def test_state_machine(
    PoolMock, accounts, registry, state_machine,
    DAI, USDC, USDT, TUSD,
    yDAI, yUSDC, yUSDT, yTUSD
):
    coins = [yDAI, yUSDC, yUSDT, yTUSD]
    underlying = [DAI, USDC, USDT, TUSD]

    state_machine(StateMachine, PoolMock, accounts, registry, coins, underlying, USDT)
