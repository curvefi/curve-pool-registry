import itertools
import math
from collections import defaultdict

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
    lending_swap,
    lp_token,
    n_coins,
    is_v1,
    rate_method_id,
    underlying_decimals,
    wrapped_decimals,
    chain,
):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    registry.add_pool(
        lending_swap,
        n_coins,
        lp_token,
        rate_method_id,
        pack_values(wrapped_decimals),
        pack_values(underlying_decimals),
        hasattr(lending_swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )
    chain.sleep(10)
    registry.remove_pool(lending_swap, {"from": alice})
    yield registry


@pytest.mark.itercoins("send", "recv")
def test_find_pool(registry, wrapped_coins, underlying_coins, send, recv):
    assert registry.find_pool_for_coins(wrapped_coins[send], wrapped_coins[recv]) == ZERO_ADDRESS
    assert (
        registry.find_pool_for_coins(underlying_coins[send], underlying_coins[recv]) == ZERO_ADDRESS
    )


def test_get_n_coins(registry, lending_swap):
    assert registry.get_n_coins(lending_swap) == [0, 0]


def test_get_coins(registry, lending_swap):
    assert registry.get_coins(lending_swap) == [ZERO_ADDRESS] * 8
    assert registry.get_underlying_coins(lending_swap) == [ZERO_ADDRESS] * 8


def test_get_decimals(registry, lending_swap):
    assert registry.get_decimals(lending_swap) == [0] * 8
    assert registry.get_underlying_decimals(lending_swap) == [0] * 8


def test_get_rates(registry, lending_swap):
    assert registry.get_rates(lending_swap) == [0] * 8


@pytest.mark.itercoins("send", "recv")
def test_get_coin_indices(registry, lending_swap, underlying_coins, wrapped_coins, send, recv):
    with brownie.reverts("No available market"):
        registry.get_coin_indices(lending_swap, wrapped_coins[send], wrapped_coins[recv])
    with brownie.reverts("No available market"):
        registry.get_coin_indices(lending_swap, underlying_coins[send], underlying_coins[recv])


@pytest.mark.once
def test_get_balances(registry, lending_swap):
    with brownie.reverts():
        registry.get_balances(lending_swap)


@pytest.mark.once
def test_get_underlying_balances(registry, lending_swap):
    with brownie.reverts():
        registry.get_underlying_balances(lending_swap)


@pytest.mark.once
def test_get_admin_balances(registry, lending_swap):
    with brownie.reverts():
        registry.get_admin_balances(lending_swap)


@pytest.mark.once
def test_get_virtual_price_from_lp_token(alice, registry, lp_token):
    with brownie.reverts():
        registry.get_virtual_price_from_lp_token(lp_token)


@pytest.mark.once
def test_get_pool_from_lp_token(registry, lp_token):
    assert registry.get_pool_from_lp_token(lp_token) == ZERO_ADDRESS


@pytest.mark.once
def test_get_lp_token(registry, lending_swap):
    assert registry.get_lp_token(lending_swap) == ZERO_ADDRESS


def test_coin_count_is_correct(registry):

    assert registry.coin_count() == 0


def test_get_all_swappable_coins(registry, wrapped_coins, underlying_coins):
    coin_set = set(map(str, itertools.chain(wrapped_coins, underlying_coins)))
    coin_count = len(coin_set)

    coins = set(registry.get_coin(i) for i in range(coin_count))

    assert coins == {ZERO_ADDRESS}


@pytest.mark.once
def test_last_updated_getter(registry, history):
    registry_txs = history.filter(receiver=registry.address)
    assert math.isclose(registry_txs[-1].timestamp, registry.last_updated())


def test_coin_swap_count(registry, wrapped_coins, underlying_coins):
    coins = set(map(str, itertools.chain(wrapped_coins, underlying_coins)))

    for coin in coins:
        assert registry.get_coin_swap_count(coin) == 0


def test_swap_coin_for(registry, wrapped_coins, underlying_coins):
    wrapped_coins = list(map(str, wrapped_coins))
    underlying_coins = list(map(str, underlying_coins))
    pairings = defaultdict(set)

    wrapped_pairs = itertools.combinations(wrapped_coins, 2)
    underlying_pairs = itertools.combinations(underlying_coins, 2)

    for coin_a, coin_b in itertools.chain(wrapped_pairs, underlying_pairs):
        pairings[coin_a].add(coin_b)
        pairings[coin_b].add(coin_a)

    for coin in pairings.keys():
        coin_swap_count = len(pairings[coin])
        available_swaps = {
            registry.get_coin_swap_complement(coin, i) for i in range(coin_swap_count)
        }

        assert available_swaps == {ZERO_ADDRESS}
