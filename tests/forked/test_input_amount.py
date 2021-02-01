import pytest
from brownie.test import given, strategy
from hypothesis import Phase, settings


@pytest.mark.itercoins("send", "recv", underlying=True)
@given(st_amount=strategy("decimal", min_value="0.5", max_value=1000, places=2))
@settings(max_examples=50, phases=[Phase.generate])
def test_get_input_amount(
    registry_swap, swap, underlying_coins, underlying_decimals, send, recv, st_amount
):
    dy = int(10 ** underlying_decimals[recv] * st_amount)

    send = underlying_coins[send]
    recv = underlying_coins[recv]

    dx = registry_swap.get_input_amount(swap, send, recv, dy)
    amount = registry_swap.get_exchange_amount(swap, send, recv, dx)
    assert abs(amount - dy) <= 1


@pytest.mark.itercoins("send", "recv")
@given(st_amount=strategy("decimal", min_value="0.5", max_value=1000, places=2))
@settings(max_examples=50, phases=[Phase.generate])
def test_get_input_amount_wrapped(
    registry_swap, swap, wrapped_coins, wrapped_decimals, send, recv, st_amount
):
    dy = int(10 ** wrapped_decimals[recv] * st_amount)

    send = wrapped_coins[send]
    recv = wrapped_coins[recv]

    dx = registry_swap.get_input_amount(swap, send, recv, dy)
    amount = registry_swap.get_exchange_amount(swap, send, recv, dx)
    assert abs(amount - dy) <= 1
