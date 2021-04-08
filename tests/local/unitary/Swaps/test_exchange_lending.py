import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def registry(
    Registry,
    provider,
    gauge_controller,
    alice,
    lending_swap,
    lp_token,
    n_coins,
    is_v1,
    rate_method_id,
):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    provider.set_address(0, registry, {"from": alice})
    registry.add_pool(
        lending_swap,
        n_coins,
        lp_token,
        rate_method_id,
        0,
        0,
        hasattr(lending_swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )
    yield registry


@pytest.fixture(scope="module")
def registry_swap(
    Swaps, alice, bob, registry, provider, lending_swap, calculator, underlying_coins, wrapped_coins
):
    contract = Swaps.deploy(provider, calculator, {"from": alice})

    for underlying, wrapped in zip(underlying_coins, wrapped_coins):
        if underlying == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            bob.transfer(lending_swap, "10 ether")
            continue
        underlying.approve(contract, 2 ** 256 - 1, {"from": alice})
        if underlying != wrapped:
            wrapped.approve(contract, 2 ** 256 - 1, {"from": alice})

    yield contract


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_exchange(alice, registry_swap, lending_swap, wrapped_coins, wrapped_decimals, send, recv):
    amount = 10 ** wrapped_decimals[send]

    send = wrapped_coins[send]
    recv = wrapped_coins[recv]
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    expected = registry_swap.get_exchange_amount(lending_swap, send, recv, amount)
    registry_swap.exchange(lending_swap, send, recv, amount, 0, {"from": alice, "value": value})

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:

        assert send.balanceOf(registry_swap) == 0
        assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:
        assert recv.balanceOf(registry_swap) == 0
        assert recv.balanceOf(alice) == expected


@pytest.mark.params(n_coins=4, lending="cERC20")
@pytest.mark.itercoins("send", "recv")
def test_exchange_underlying(
    alice, registry_swap, lending_swap, underlying_coins, underlying_decimals, send, recv
):
    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    expected = registry_swap.get_exchange_amount(lending_swap, send, recv, amount)
    registry_swap.exchange(lending_swap, send, recv, amount, 0, {"from": alice, "value": value})

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:

        assert send.balanceOf(registry_swap) == 0
        assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:
        assert recv.balanceOf(registry_swap) == 0
        assert recv.balanceOf(alice) == expected


@pytest.mark.params(n_coins=4, lending="cERC20")
@pytest.mark.itercoins("send", "recv")
def test_min_expected(
    alice, registry_swap, lending_swap, underlying_coins, underlying_decimals, send, recv
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

    expected = registry_swap.get_exchange_amount(lending_swap, send, recv, amount)
    with brownie.reverts():
        registry_swap.exchange(
            lending_swap, send, recv, amount, expected + 1, {"from": alice, "value": value}
        )
