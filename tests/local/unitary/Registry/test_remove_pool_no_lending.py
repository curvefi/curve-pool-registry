import math

import brownie
import pytest

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def registry(
    Registry,
    provider,
    gauge_controller,
    alice,
    swap,
    lp_token,
    n_coins,
    is_v1,
    underlying_decimals,
    chain,
):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    registry.add_pool_without_underlying(
        swap,
        n_coins,
        lp_token,
        "0x00",
        pack_values(underlying_decimals),
        0,  # use rates
        hasattr(swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )
    chain.sleep(10)
    registry.remove_pool(swap, {"from": alice})
    yield registry


@pytest.mark.itercoins("send", "recv")
def test_find_pool(registry, underlying_coins, send, recv):
    assert (
        registry.find_pool_for_coins(underlying_coins[send], underlying_coins[recv]) == ZERO_ADDRESS
    )


def test_get_n_coins(registry, swap):
    assert registry.get_n_coins(swap) == [0, 0]


def test_get_coins(registry, swap):
    assert registry.get_coins(swap) == [ZERO_ADDRESS] * 8
    assert registry.get_underlying_coins(swap) == [ZERO_ADDRESS] * 8


def test_get_decimals(registry, swap):
    assert registry.get_decimals(swap) == [0] * 8
    assert registry.get_underlying_decimals(swap) == [0] * 8


def test_get_rates(registry, swap):
    assert registry.get_rates(swap) == [0] * 8


@pytest.mark.itercoins("send", "recv")
def test_get_coin_indices(registry, swap, underlying_coins, send, recv):
    with brownie.reverts("No available market"):
        registry.get_coin_indices(swap, underlying_coins[send], underlying_coins[recv])


@pytest.mark.once
def test_get_balances(registry, swap):
    with brownie.reverts():
        registry.get_balances(swap)


@pytest.mark.once
def test_get_underlying_balances(registry, swap):
    with brownie.reverts():
        registry.get_underlying_balances(swap)


@pytest.mark.once
def test_get_admin_balances(registry, swap):
    with brownie.reverts():
        registry.get_admin_balances(swap)


@pytest.mark.once
def test_get_virtual_price_from_lp_token(alice, registry, lp_token):
    with brownie.reverts():
        registry.get_virtual_price_from_lp_token(lp_token)


@pytest.mark.once
def test_get_pool_from_lp_token(registry, lp_token):
    assert registry.get_pool_from_lp_token(lp_token) == ZERO_ADDRESS


@pytest.mark.once
def test_get_lp_token(registry, swap):
    assert registry.get_lp_token(swap) == ZERO_ADDRESS


def test_coin_count_is_correct(registry):

    assert registry.coin_count() == 0


def test_get_all_swappable_coins(registry, underlying_coins):
    coin_count = len(underlying_coins)

    coins = set(registry.get_coin(i) for i in range(coin_count))

    assert coins == {ZERO_ADDRESS}


@pytest.mark.once
def test_last_updated_getter(registry, history):
    registry_txs = history.filter(receiver=registry.address)
    assert math.isclose(
        registry_txs[-1].timestamp, registry.last_updated(), rel_tol=0.001, abs_tol=4
    )


def test_coin_swap_count(registry, underlying_coins):
    for coin in underlying_coins:
        assert registry.get_coin_swap_count(coin) == 0


def test_swap_coin_for(registry, underlying_coins):
    coin_set = set(map(str, underlying_coins))

    for coin in coin_set:
        coin_swap_count = len(coin_set) - 1
        swap_coins = {registry.get_coin_swap_complement(coin, i) for i in range(coin_swap_count)}

        assert swap_coins == {ZERO_ADDRESS}
