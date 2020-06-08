from brownie.test import given, strategy
from hypothesis import settings


@given(st_amounts=strategy("uint[50]", min_value=10**5, max_value=10**8, unique=True))
@settings(max_examples=10)
def test_get_amounts(registry_renbtc, accounts, pool_renbtc, RenBTC, WBTC, st_amounts):
    amounts = registry_renbtc.get_exchange_amounts.call(
        pool_renbtc,
        RenBTC,
        WBTC,
        st_amounts,
    )
    for i in range(50):
        amount = registry_renbtc.get_exchange_amount(pool_renbtc, RenBTC, WBTC, st_amounts[i])
        assert amount == amounts[i]


@given(st_amounts=strategy("uint[50]", min_value=10**5, max_value=10**8, unique=True))
@settings(max_examples=10)
def test_get_amounts_reversed(registry_renbtc, accounts, pool_renbtc, RenBTC, WBTC, st_amounts):
    amounts = registry_renbtc.get_exchange_amounts.call(
        pool_renbtc,
        WBTC,
        RenBTC,
        st_amounts,
    )
    for i in range(50):
        amount = registry_renbtc.get_exchange_amount(pool_renbtc, WBTC, RenBTC, st_amounts[i])
        assert amount == amounts[i]
