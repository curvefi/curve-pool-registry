.. _registry:


========
Registry
========

``Registry`` is the main registry contract. It is used to locate pools and query information about them.

Source code for this contract is available on `Github <https://github.com/curvefi/curve-pool-registry/blob/master/contracts/Registry.vy>`_.

View Functions
==============

Because Vyper does not support dynamic-length arrays, all arrays have a fixed length. Excess fields contain zero values.

Finding Pools
-------------

.. py:function:: Registry.pool_count() -> uint256: view

    The number of pools currently registered within the contract.

        .. code-block:: python

            >>> registry.pool_count()
            18


.. py:function:: Registry.pool_list(i: uint256) -> address: view

    Master list of registered pool addresses.

    Note that the ordering of this list is not fixed. Index values of addresses may change as pools are added or removed.

    Querying values greater than `Registry.pool_count` returns ``0x00``.

        .. code-block:: python

            >>> registry.pool_list(7)
            '0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6'

.. py:function:: Registry.get_pool_from_lp_token(lp_token: address) -> address: view

    Get the pool address for a given Curve LP token.

        .. code-block:: python

            >>> registry.get_pool_from_lp_token('0x1AEf73d49Dedc4b1778d0706583995958Dc862e6')
            '0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6'

.. py:function:: Registry.get_lp_token(pool: address) -> address: view

    Get the LP token address for a given Curve pool.

        .. code-block:: python

            >>> registry.get_lp_token('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6')
            '0x1AEf73d49Dedc4b1778d0706583995958Dc862e6'

.. py:function:: Registry.find_pool_for_coins(_from: address, _to: address, i: uint256 = 0) -> address: view

    Finds a pool that allows for swaps between ``_from`` and ``_to``. You can optionally include ``i`` to get the n-th pool, when multiple pools exist for the given pairing.

    The order of ``_from`` and ``_to`` does not affect the result.

    Returns ``0x00`` when swaps are not possible for the pair or ``i`` exceeds the number of available pools.

        .. code-block:: python

            >>> registry.find_pool_for_coins('0x6b175474e89094c44da98b954eedeac495271d0f', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
            '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7'

            >>> registry.find_pool_for_coins('0x6b175474e89094c44da98b954eedeac495271d0f', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 1)
            '0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27'

Getting Info About a Pool
-------------------------

Coins and Coin Info
*******************

.. py:function:: Registry.get_n_coins(pool: address) -> uint256[2]: view

    Get the number of coins and underlying coins within a pool.

        .. code-block:: python

            >>> registry.get_n_coins('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6')
            (2, 4)

.. py:function:: Registry.get_coins(pool: address) -> address[8]: view

    Get a list of the swappable coins within a pool.

        .. code-block:: python

            >>> registry.get_coins('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6')
            ("0xe2f2a5C287993345a840Db3B0845fbC70f5935a5", "0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000")

.. py:function:: Registry.get_underlying_coins(pool: address) -> address[8]: view

    Get a list of the swappable underlying coins within a pool.

    For pools that do not involve lending, the return value is identical to :func:`Registry.get_coins <Registry.get_coins>`.

        .. code-block:: python

            >>> registry.get_underlying_coins('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6')
            ("0xe2f2a5C287993345a840Db3B0845fbC70f5935a5", "0x6B175474E89094C44Da98b954EedeAC495271d0F", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "0xdAC17F958D2ee523a2206206994597C13D831ec7", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000", "0x0000000000000000000000000000000000000000")

.. py:function:: Registry.get_decimals(pool: address) -> uint256[8]: view

    Get a list of decimal places for each coin within a pool.

        .. code-block:: python

            >>> registry.get_decimals('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6')
            (18, 18, 0, 0, 0, 0, 0, 0)

.. py:function:: Registry.get_underlying_decimals(pool: address) -> uint256[8]: view

    Get a list of decimal places for each underlying coin within a pool.

    For pools that do not involve lending, the return value is identical to :func:`Registry.get_decimals <Registry.get_decimals>`.  Non-lending coins that still involve querying a rate (e.g. renBTC) are marked as having ``0`` decimals.

        .. code-block:: python

            >>> registry.get_underlying_decimals('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6')
            (18, 18, 6, 6, 0, 0, 0, 0)

.. py:function:: Registry.get_coin_indices(pool: address, _from: address, _to: address) -> (int128, int128, bool): view

    Convert coin addresses into indices for use with pool methods.

    Returns the index of ``_from``, index of ``_to``, and a boolean indicating if the coins are considered underlying in the given pool.

        .. code-block:: python

            >>> registry.get_coin_indices('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27', '0xdac17f958d2ee523a2206206994597c13d831ec7', '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
            (2, 1, True)

    Based on the above call, we know:

        * the index of the coin we are swapping out of is ``2``
        * the index of the coin we are swapping into is ``1``
        * the coins are considred underlying, so we must call ``exchange_underlying``

    From this information we can perform a token swap:

        .. code-block:: python

            >>> swap = Contract('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            >>> swap.exchange_underlying(2, 1, 1e18, 0, {'from': alice})


Balances and Rates
******************

.. py:function:: Registry.get_balances(pool: address) -> uint256[8]: view

    Get available balances for each coin within a pool.

    These values are not necessarily the same as calling ``Token.balanceOf(pool)`` as the total balance also includes unclaimed admin fees.

        .. code-block:: python

            >>> registry.get_balances('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            (11428161394428689823275227, 47831326741306, 45418708932136, 48777578907442492245548483, 0, 0, 0, 0)

.. py:function:: Registry.get_underlying_balances(pool: address) -> uint256[8]: view

    Get balances for each underlying coin within a pool.

    For pools that do not involve lending, the return value is identical to :func:`Registry.get_balances <Registry.get_balances>`.

        .. code-block:: python

            >>> registry.get_underlying_balances('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            (11876658145799734093379928, 48715210997790596223520238, 46553896776332824101242804, 49543896565857325657915396, 0, 0, 0, 0)

.. py:function:: Registry.get_admin_balances(pool: address) -> uint256[8]: view

    Get the current admin balances (uncollected fees) for a pool.

        .. code-block:: python

            >>> registry.get_admin_balances('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            (10800690926373756722358, 30891687335, 22800662409, 16642955874751891466129, 0, 0, 0, 0)

.. py:function:: Registry.get_rates(pool: address) -> uint256[8]: view

    Get the exchange rates between coins and underlying coins within a pool, normalized to a ``1e18`` precision.

    For non-lending pools or non-lending coins within a lending pool, the rate is ``1e18``.

        .. code-block:: python

            >>> registry.get_rates('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            (1039244956550111510, 1018479293504725874, 1024993895758183341, 1015710454247817308, 0, 0, 0, 0)

.. py:function:: Registry.get_virtual_price_from_lp_token(lp_token: address) -> uint256: view

    Get the virtual price of a pool LP token.

        .. code-block:: python

            >>> registry.get_virtual_price_from_lp_token('0x3B3Ac5386837Dc563660FB6a0937DFAa5924333B')
            1060673685385893596

Pool Parameters
***************

.. py:function:: Registry.get_A(pool: address) -> uint256: view

    Get the current amplification coefficient for a pool.

        .. code-block:: python

            >>> registry.get_A('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            500

.. py:function:: Registry.get_fees(pool: address) -> uint256[2]: view

    Get the fees for a pool.

    Fees are expressed as integers with a ``1e10`` precision. The first value is the total fee, the second is the percentage of the fee taken as an admin fee.

    A typical return value here is ``(4000000, 5000000000)`` - a 0.04% fee, 50% of which is taken as an admin fee.

        .. code-block:: python

            >>> registry.get_fees('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            (4000000, 5000000000)

.. py:function:: Registry.get_parameters(pool: address) -> PoolParams: view

    Get all parameters for a given pool.

    The return value is a struct, organized as follows:

        .. code-block:: python

            struct PoolParams:
                A: uint256
                future_A: uint256
                fee: uint256
                admin_fee: uint256
                future_fee: uint256
                future_admin_fee: uint256
                future_owner: address
                initial_A: uint256
                initial_A_time: uint256
                future_A_time: uint256

    Note that for older pools where ``initial_A`` is not public, this value is set to ``0``.

        .. code-block:: python

            >>> registry.get_parameters('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27').dict()
            {
                'A': 500,
                'admin_fee': 5000000000,
                'fee': 4000000,
                'future_A': 500,
                'future_A_time': 0,
                'future_admin_fee': 5000000000,
                'future_fee': 4000000,
                'future_owner': "0x56295b752e632f74a6526988eaCE33C25c52c623",
                'initial_A': 0,
                'initial_A_time': 0
            }

Gas Estimates
*************

.. py:function:: Registry.estimate_gas_used(pool: address, _from: address, _to: address) -> uint256: view

    Get an estimate on the upper bound for gas used in an exchange.

Gauges
------

.. py:function:: Registry.gauge_controller() -> address: view

    Get the address of the Curve DAO `GaugeController <https://github.com/curvefi/curve-dao-contracts/blob/master/contracts/GaugeController.vy>`_ contract.

        .. code-block:: python

            >>> registry.gauge_controller()
            '0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB'

.. py:function:: Registry.get_gauges(pool: address) -> (address[10], int128[10]): view

    Get a list of `LiquidityGauge <https://github.com/curvefi/curve-contract/tree/master/contracts/gauges>`_ contracts associated with a pool, and their gauge types.

        .. code-block:: python

            >>> registry.get_gauges('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27')
            (('0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000'), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
