import itertools
import math
from collections import Counter, defaultdict

import brownie
import pytest

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True, params=["meta", "factory"])
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
    underlying_decimals,
    meta_decimals,
    chain,
    request,
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
    registry.add_metapool(
        meta_swap,
        n_metacoins,
        meta_lp_token,
        pack_values(meta_decimals),
        "",
        ZERO_ADDRESS if request.param == "meta" else swap,
        {"from": alice},
    )
    chain.sleep(10)
    registry.remove_pool(meta_swap, {"from": alice})
    yield registry


def test_find_pool(registry, meta_coins, underlying_coins, n_metacoins):
    for i, j in itertools.combinations(range(n_metacoins), 2):
        assert registry.find_pool_for_coins(meta_coins[i], meta_coins[j]) == ZERO_ADDRESS

    for meta, base in itertools.product(meta_coins[:-1], underlying_coins):
        assert registry.find_pool_for_coins(meta, base) == ZERO_ADDRESS


def test_get_n_coins(registry, meta_swap):
    assert registry.get_n_coins(meta_swap) == [0, 0]


def test_get_coins(registry, meta_swap, meta_coins):
    assert registry.get_coins(meta_swap) == [ZERO_ADDRESS] * 8
    assert registry.get_underlying_coins(meta_swap) == [ZERO_ADDRESS] * 8


def test_get_decimals(registry, meta_swap):
    assert registry.get_decimals(meta_swap) == [0] * 8
    assert registry.get_underlying_decimals(meta_swap) == [0] * 8


def test_get_rates(registry, meta_swap):
    assert registry.get_rates(meta_swap) == [0] * 8


def test_get_coin_indices(registry, meta_swap, underlying_coins, meta_coins, n_coins, n_metacoins):
    for i, j in itertools.combinations(range(n_metacoins), 2):
        with brownie.reverts("No available market"):
            registry.get_coin_indices(meta_swap, meta_coins[i], meta_coins[j])

    coins = meta_coins[:-1] + underlying_coins
    for i, j in itertools.product(range(n_coins - 1), range(n_coins, n_coins + n_metacoins - 1)):
        with brownie.reverts("No available market"):
            registry.get_coin_indices(meta_swap, coins[i], coins[j])


@pytest.mark.once
def test_get_balances(registry, meta_swap):
    with brownie.reverts():
        registry.get_balances(meta_swap)


@pytest.mark.once
def test_get_underlying_balances(registry, meta_swap):
    with brownie.reverts():
        registry.get_underlying_balances(meta_swap)


@pytest.mark.once
def test_get_admin_balances(registry, meta_swap):
    with brownie.reverts():
        registry.get_admin_balances(meta_swap)


@pytest.mark.once
def test_get_virtual_price_from_lp_token(alice, registry, meta_lp_token):
    with brownie.reverts():
        registry.get_virtual_price_from_lp_token(meta_lp_token)


@pytest.mark.once
def test_get_pool_from_lp_token(registry, meta_lp_token):
    assert registry.get_pool_from_lp_token(meta_lp_token) == ZERO_ADDRESS


@pytest.mark.once
def test_get_lp_token(registry, meta_swap):
    assert registry.get_lp_token(meta_swap) == ZERO_ADDRESS


def test_coin_count_is_correct(registry, underlying_coins):

    assert registry.coin_count() == len(underlying_coins)


def test_get_all_swappable_coins(registry, meta_coins, underlying_coins):
    coin_set = set(map(str, itertools.chain(meta_coins, underlying_coins)))
    coin_count = len(coin_set)

    coins = set(registry.get_coin(i) for i in range(coin_count))

    assert coins == set(map(str, underlying_coins)) | {ZERO_ADDRESS}


@pytest.mark.once
def test_last_updated_getter(registry, history):
    registry_txs = history.filter(receiver=registry.address)
    assert math.isclose(registry_txs[-1].timestamp, registry.last_updated())


def test_coin_swap_count(registry, meta_coins, underlying_coins):
    meta_coins = list(map(str, meta_coins))
    underlying_coins = list(map(str, underlying_coins))
    counter = Counter()

    underlying_pairs = itertools.chain(*itertools.combinations(underlying_coins, 2))

    counter.update(underlying_pairs)

    for coin in meta_coins:
        assert registry.get_coin_swap_count(coin) == 0

    for coin in underlying_coins:
        assert registry.get_coin_swap_count(coin) == counter[coin]


def test_swap_coin_for(registry, meta_coins, underlying_coins):
    meta_coins = list(map(str, meta_coins))
    underlying_coins = list(map(str, underlying_coins))
    pairings = defaultdict(set)

    underlying_pairs = list(itertools.combinations(map(str, underlying_coins), 2))

    for coin_a, coin_b in underlying_pairs:
        pairings[coin_a].add(coin_b)
        pairings[coin_b].add(coin_a)

    for coin in itertools.chain(meta_coins, underlying_coins):
        coin_swap_count = len(pairings[coin])
        available_swaps = {
            registry.get_coin_swap_complement(coin, i) for i in range(coin_swap_count)
        }

        assert available_swaps == pairings[coin]
