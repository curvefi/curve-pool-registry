import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def registry(
    Registry,
    provider,
    gauge_controller,
    alice,
    swap,
    meta_swap,
    lp_token,
    meta_lp_token,
    n_coins,
    n_metacoins,
    is_v1,
):
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
    registry.add_metapool(meta_swap, n_metacoins, meta_lp_token, 0, "", {"from": alice})
    yield registry


@pytest.fixture(scope="module")
def registry_swap(
    Swaps, alice, bob, registry, provider, meta_swap, calculator, underlying_coins, meta_coins
):
    contract = Swaps.deploy(provider, calculator, {"from": alice})

    for coin in underlying_coins:
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            bob.transfer(meta_swap, "10 ether")
        else:
            coin.approve(contract, 2 ** 256 - 1, {"from": alice})
    for coin in meta_coins:
        coin.approve(contract, 2 ** 256 - 1, {"from": alice})

    yield contract


@pytest.mark.params(n_coins=4, n_metacoins=4)
@pytest.mark.itermetacoins("send", "recv")
def test_exchange(alice, registry_swap, meta_swap, meta_coins, meta_decimals, send, recv):
    amount = 10 ** meta_decimals[send]

    send = meta_coins[send]
    recv = meta_coins[recv]
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    expected = registry_swap.get_exchange_amount(meta_swap, send, recv, amount)
    registry_swap.exchange(meta_swap, send, recv, amount, 0, {"from": alice, "value": value})

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


@pytest.mark.params(n_coins=4, n_metacoins=4)
@pytest.mark.itermetacoins("send", max=2)
@pytest.mark.itercoins("recv")
def test_meta_to_base(
    alice, registry_swap, meta_swap, meta_coins, underlying_coins, meta_decimals, send, recv
):
    amount = 10 ** meta_decimals[send]

    send = meta_coins[send]
    recv = underlying_coins[recv]

    send._mint_for_testing(alice, amount, {"from": alice})

    expected = registry_swap.get_exchange_amount(meta_swap, send, recv, amount)
    registry_swap.exchange(meta_swap, send, recv, amount, 0, {"from": alice})

    assert send.balanceOf(registry_swap) == 0
    assert send.balanceOf(alice) == 0

    if recv == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:
        assert recv.balanceOf(registry_swap) == 0
        assert recv.balanceOf(alice) == expected


@pytest.mark.params(n_coins=4, n_metacoins=4)
@pytest.mark.itercoins("send")
@pytest.mark.itermetacoins("recv", max=2)
def test_base_to_meta(
    alice, registry_swap, meta_swap, meta_coins, underlying_coins, underlying_decimals, send, recv
):
    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = meta_coins[recv]

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        value = 0
        send._mint_for_testing(alice, amount, {"from": alice})

    expected = registry_swap.get_exchange_amount(meta_swap, send, recv, amount)
    registry_swap.exchange(meta_swap, send, recv, amount, 0, {"from": alice, "value": value})

    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        assert registry_swap.balance() == 0
    else:
        assert send.balanceOf(registry_swap) == 0
        assert send.balanceOf(alice) == 0

    assert recv.balanceOf(registry_swap) == 0
    assert recv.balanceOf(alice) == expected


@pytest.mark.params(n_coins=4, n_metacoins=4)
@pytest.mark.itercoins("send", "recv")
def test_exchange_underlying(
    alice, registry_swap, meta_swap, underlying_coins, underlying_decimals, send, recv
):
    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]
    if send == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        value = 10 ** 18
    else:
        send._mint_for_testing(alice, amount, {"from": alice})
        value = 0

    expected = registry_swap.get_exchange_amount(meta_swap, send, recv, amount)
    registry_swap.exchange(meta_swap, send, recv, amount, 0, {"from": alice, "value": value})

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
