import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def registry(Registry, provider, gauge_controller, alice, swap, lp_token, n_coins, is_v1):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    provider.set_address(0, registry, {"from": alice})
    registry.add_pool_without_underlying(
        swap,
        n_coins,
        lp_token,
        "0x00",
        0,
        0,  # use rates
        hasattr(swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )
    yield registry


@pytest.fixture(scope="module")
def registry_swap(Swaps, alice, bob, registry, provider, swap, calculator, underlying_coins):
    contract = Swaps.deploy(provider, calculator, {"from": alice})

    for coin in underlying_coins:
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            bob.transfer(swap, "10 ether")
        else:
            coin.approve(contract, 2 ** 256 - 1, {"from": alice})

    yield contract


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_exchange(alice, registry_swap, swap, underlying_coins, underlying_decimals, send, recv):

    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        eth_balance = alice.balance()

    expected = registry_swap.get_exchange_amount(swap, send, recv, amount)
    registry_swap.exchange(swap, send, recv, amount, 0, {"from": alice, "value": value})

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:

        assert send.balanceOf(registry_swap) == 0
        assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
        assert alice.balance() > eth_balance
    else:
        assert recv.balanceOf(registry_swap) == 0
        assert recv.balanceOf(alice) == expected


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_existing_balance(
    alice, bob, registry_swap, swap, underlying_coins, underlying_decimals, send, recv
):
    # an existing balance within the contact should not affect the outcome of an exchange
    amount = 10 ** underlying_decimals[send]
    send = underlying_coins[send]
    recv = underlying_coins[recv]

    bob.transfer(registry_swap, "10 ether")
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        send._mint_for_testing(registry_swap, 10 ** 19, {"from": alice})
        value = 0

    if recv != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        recv._mint_for_testing(registry_swap, 10 ** 19, {"from": alice})

    registry_swap.exchange(swap, send, recv, amount, 0, {"from": alice, "value": value})

    assert registry_swap.balance() == "10 ether"
    if send != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert send.balanceOf(registry_swap) == 10 ** 19
    if recv != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert recv.balanceOf(registry_swap) == 10 ** 19


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
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


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_existing_balance_insufficient_send(
    alice, bob, registry_swap, swap, underlying_coins, underlying_decimals, send, recv
):
    # insuffucient send amount should fail an exchange, even when the contract has
    # an existing balance that would cover the remainder!
    amount = 10 ** underlying_decimals[send]
    send = underlying_coins[send]
    recv = underlying_coins[recv]

    bob.transfer(registry_swap, "10 ether")
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18 - 1
    else:
        send._mint_for_testing(alice, amount - 1, {"from": alice})
        send._mint_for_testing(registry_swap, 10 ** 19, {"from": alice})
        value = 0

    if recv != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        recv._mint_for_testing(registry_swap, 10 ** 19, {"from": alice})

    with brownie.reverts():
        registry_swap.exchange(swap, send, recv, amount, 0, {"from": alice, "value": value})


@pytest.mark.params(n_coins=2)
@pytest.mark.itercoins("send", "recv")
def test_receiver(
    alice, bob, registry_swap, swap, underlying_coins, underlying_decimals, send, recv
):

    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0
    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        eth_balance = bob.balance()

    expected = registry_swap.get_exchange_amount(swap, send, recv, amount)
    registry_swap.exchange(swap, send, recv, amount, 0, bob, {"from": alice, "value": value})

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:

        assert send.balanceOf(registry_swap) == 0
        assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
        assert bob.balance() > eth_balance
    else:
        assert recv.balanceOf(registry_swap) == 0
        assert recv.balanceOf(alice) == 0
        assert recv.balanceOf(bob) == expected
