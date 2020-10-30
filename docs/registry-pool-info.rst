.. _address-provider:

=========
Pool Info
=========

``PoolInfo`` contains aggregate getter methods for querying large data sets about a single pool. It is designed for off-chain use (not optimized for gas efficiency).

Source code for this contract is available on `Github <https://github.com/curvefi/curve-pool-registry/blob/master/contracts/PoolInfo.vy>`_.

View Functions
==============

.. py:function:: PoolInfo.get_pool_coins(pool: address) -> address[8], address[8], uint256[8], uint256[8]: view

    Get information about the coins in a pool.

    The return data is structured as follows:

    * ``address[8]``: Coin addresses
    * ``address[8]``: Underlying coin addresses
    * ``uint256[8]``: Coin decimal places
    * ``uint256[8]``: Coin underlying decimal places

    .. code-block:: python

        >>> pool_info.get_pool_coins('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27').dict()
        {
            'coins': (
                "0xC2cB1040220768554cf699b0d863A3cd4324ce32",
                "0x26EA744E5B887E5205727f55dFBE8685e3b21951",
                "0xE6354ed5bC4b393a5Aad09f21c46E101e692d447",
                "0x04bC0Ab673d88aE9dbC9DA2380cB6B79C4BCa9aE",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000"
            ),
            'decimals': (18, 6, 6, 18, 0, 0, 0, 0),
            'underlying_coins': (
                "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "0x4Fabb145d64652a948d72533023f6E7A623C7C53",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000"
            ),
            'underlying_decimals': (18, 6, 6, 18, 0, 0, 0, 0)
        }

.. py:function:: PoolInfo.get_pool_info(pool: address) -> PoolInfo: view

    Query information about a pool.

    The return data is formatted using the following structs:

    .. code-block:: python

        struct PoolInfo:
            balances: uint256[MAX_COINS]
            underlying_balances: uint256[MAX_COINS]
            decimals: uint256[MAX_COINS]
            underlying_decimals: uint256[MAX_COINS]
            rates: uint256[MAX_COINS]
            lp_token: address
            params: PoolParams

        # this struct is nested inside `PoolInfo`
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

    An example query:

    .. code-block:: python

        >>> pool_info.get_pool_info('0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27').dict()
        {
            'balances': (11428161394428689823275227, 47831326741306, 45418708932136, 48777578907442492245548483, 0, 0, 0, 0),
            'decimals': (18, 6, 6, 18, 0, 0, 0, 0),
            'lp_token': "0x3B3Ac5386837Dc563660FB6a0937DFAa5924333B",
            'params': (500, 500, 4000000, 5000000000, 4000000, 5000000000, "0x56295b752e632f74a6526988eaCE33C25c52c623", 0, 0, 0),
            'rates': (1039246194444517276, 1018480818866816704, 1024994762508449404, 1015710534981182027, 0, 0, 0, 0),
            'underlying_balances': (11876673238657763875985115, 48715288826971602262153927, 46553938775335128958626025, 49543900767165234117573778, 0, 0, 0, 0),
            'underlying_decimals': (18, 6, 6, 18, 0, 0, 0, 0)
        }
