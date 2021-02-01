import pytest
from brownie.test import given, strategy
from hypothesis import Phase, settings


@pytest.mark.itercoins("send", "recv")
@given(st_amounts=strategy("decimal[100]", min_value="0.05", max_value=10, places=2, unique=True))
@settings(max_examples=3, phases=[Phase.generate])
def test_get_amounts_wrapped(
    registry_swap, swap, wrapped_coins, wrapped_decimals, send, recv, st_amounts
):
    base_amount = 10 ** wrapped_decimals[send]
    st_amounts = [int(base_amount * i) for i in st_amounts]

    send = wrapped_coins[send]
    recv = wrapped_coins[recv]

    amounts = registry_swap.get_exchange_amounts(swap, send, recv, st_amounts)

    for i in range(100):
        # `get_exchange_amount` is a thin wrapper that calls `swap.get_dy`
        amount = registry_swap.get_exchange_amount(swap, send, recv, st_amounts[i])
        assert abs(amount - amounts[i]) <= 1


@pytest.mark.itercoins("send", "recv", underlying=True)
@given(st_amounts=strategy("decimal[100]", min_value="0.05", max_value=10, places=2, unique=True))
@settings(max_examples=3, phases=[Phase.generate])
def test_get_amounts_underlying(
    registry_swap, swap, underlying_coins, underlying_decimals, send, recv, st_amounts
):
    base_amount = 10 ** underlying_decimals[send]
    st_amounts = [int(base_amount * i) for i in st_amounts]

    send = underlying_coins[send]
    recv = underlying_coins[recv]

    amounts = registry_swap.get_exchange_amounts(swap, send, recv, st_amounts)

    for i in range(100):
        # `get_exchange_amount` is a thin wrapper that calls `swap.get_dy_underlying`
        amount = registry_swap.get_exchange_amount(swap, send, recv, st_amounts[i])
        assert abs(amount - amounts[i]) <= 1
