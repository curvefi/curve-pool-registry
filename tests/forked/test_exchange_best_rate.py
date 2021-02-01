import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS


@pytest.fixture(scope="module")
def provider(AddressProvider):
    yield AddressProvider.at("0x0000000022D53366457F9d5E68Ec105046FC4383")


@pytest.fixture(scope="module")
def registry_swap(Swaps, alice, provider, calculator, underlying_coins, wrapped_coins):
    yield Swaps.deploy(provider, ZERO_ADDRESS, {"from": alice})


@pytest.mark.itercoins("send", "recv", underlying=True)
def test_exchange(
    alice, bob, registry_swap, swap, underlying_coins, underlying_decimals, send, recv
):
    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]
    balance = bob.balance()
    value = 10 ** 18 if send == ETH_ADDRESS else 0
    if send != ETH_ADDRESS:
        send.approve(registry_swap, 2 ** 256 - 1, {"from": alice})
        send._mint_for_testing(alice, amount, {"from": alice})

    registry_swap.exchange_with_best_rate(
        send, recv, amount, 0, bob, {"from": alice, "value": value}
    )

    # we don't verify the amounts here, just that the expected tokens were exchanged
    if send == ETH_ADDRESS:
        assert alice.balance() < balance
    else:
        assert send.balanceOf(alice) == 0

    if recv == ETH_ADDRESS:
        assert bob.balance() > balance
    else:
        assert recv.balanceOf(bob) > 0


@pytest.mark.itercoins("send", "recv")
def test_exchange_wrapped(alice, bob, registry_swap, wrapped_coins, wrapped_decimals, send, recv):
    amount = 10 ** wrapped_decimals[send]

    send = wrapped_coins[send]
    recv = wrapped_coins[recv]
    balance = alice.balance()
    value = 10 ** 18 if send == ETH_ADDRESS else 0
    if send != ETH_ADDRESS:
        send.approve(registry_swap, 2 ** 256 - 1, {"from": alice})
        send._mint_for_testing(alice, amount, {"from": alice})

    registry_swap.exchange_with_best_rate(
        send, recv, amount, 0, bob, {"from": alice, "value": value}
    )

    if send == ETH_ADDRESS:
        assert alice.balance() < balance
    else:
        assert send.balanceOf(alice) == 0

    if recv == ETH_ADDRESS:
        assert bob.balance() > balance
    else:
        assert recv.balanceOf(bob) > 0
