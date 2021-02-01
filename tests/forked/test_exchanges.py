import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def initial_approvals(registry_swap, alice, underlying_coins):
    for coin in underlying_coins:
        if coin != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            coin.approve(registry_swap, 2 ** 256 - 1, {"from": alice})


@pytest.mark.itercoins("send", "recv", underlying=True)
def test_exchange(alice, registry_swap, swap, underlying_coins, underlying_decimals, send, recv):
    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]
    balance = alice.balance()
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    registry_swap.exchange(swap, send, recv, amount, 0, {"from": alice, "value": value})

    # we don't verify the amounts here, just that the expected tokens were exchanged
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert alice.balance() < balance
    else:
        assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert alice.balance() > balance
    else:
        assert recv.balanceOf(alice) > 0


@pytest.mark.itercoins("send", "recv")
def test_exchange_wrapped(alice, registry_swap, swap, wrapped_coins, wrapped_decimals, send, recv):
    amount = 10 ** wrapped_decimals[send]

    send = wrapped_coins[send]
    recv = wrapped_coins[recv]
    balance = alice.balance()
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    registry_swap.exchange(swap, send, recv, amount, 0, {"from": alice, "value": value})

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert alice.balance() < balance
    else:
        assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert alice.balance() > balance
    else:
        assert recv.balanceOf(alice) > 0


@pytest.mark.itercoins("send", "recv", underlying=True)
def test_min_expected(
    alice, registry_swap, swap, underlying_coins, underlying_decimals, send, recv
):
    # exchange should revert when `expected` is higher than received amount
    amount = 10 ** underlying_decimals[send]
    send = underlying_coins[send]
    recv = underlying_coins[recv]

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    expected = registry_swap.get_exchange_amount(swap, send, recv, amount)
    with brownie.reverts():
        registry_swap.exchange(
            swap, send, recv, amount, expected + 1, {"from": alice, "value": value}
        )
