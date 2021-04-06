import itertools
import math
from collections import Counter, defaultdict

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
    # A factory pool is essentially a metapool, the default for base_pool arg
    # is ZERO_ADDRESS so we can use a ternary to just switch between testing
    # explicitly setting the base_pool arg
    registry.add_metapool(
        meta_swap,
        n_metacoins,
        meta_lp_token,
        pack_values(meta_decimals),
        "Meta Swap",
        ZERO_ADDRESS if request.param == "meta" else swap,
        {"from": alice},
    )
    provider.set_address(0, registry, {"from": alice})
    yield registry


@pytest.mark.itercoins("idx")
def test_find_pool_meta_with_underlying(registry, meta_coins, meta_swap, underlying_coins, idx):
    for meta in meta_coins[:-1]:
        assert registry.find_pool_for_coins(meta, underlying_coins[idx]) == meta_swap


@pytest.mark.params(n_metacoins=4, n_coins=2)
@pytest.mark.itermetacoins("send", "recv")
def test_find_pool_meta(registry, meta_swap, meta_coins, send, recv):
    assert registry.find_pool_for_coins(meta_coins[send], meta_coins[recv]) == meta_swap


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("idx")
def test_find_pool_not_exists_lp_token_with_underlying(registry, meta_coins, underlying_coins, idx):
    assert registry.find_pool_for_coins(meta_coins[-1], underlying_coins[idx]) == ZERO_ADDRESS


@pytest.mark.params(n_metacoins=4, n_coins=4)
@pytest.mark.itercoins("idx")
def test_find_pool_not_exists(registry, underlying_coins, idx):
    assert (
        registry.find_pool_for_coins(underlying_coins[idx], underlying_coins[idx]) == ZERO_ADDRESS
    )


@pytest.mark.itermetacoins("idx")
def test_find_pool_not_exists_meta(registry, meta_coins, idx):
    assert registry.find_pool_for_coins(meta_coins[idx], meta_coins[idx]) == ZERO_ADDRESS


def test_get_n_coins(registry, meta_swap, n_coins, n_metacoins):
    assert registry.get_n_coins(meta_swap) == [n_metacoins, n_coins + n_metacoins - 1]


def test_get_coins(registry, meta_swap, meta_coins, n_metacoins):
    assert registry.get_coins(meta_swap) == meta_coins + [ZERO_ADDRESS] * (8 - n_metacoins)


def test_get_underlying_coins(registry, meta_swap, meta_coins, underlying_coins):
    expected = meta_coins[:-1] + underlying_coins
    expected += [ZERO_ADDRESS] * (8 - len(expected))
    assert registry.get_underlying_coins(meta_swap) == expected


def test_get_decimals(registry, registry_pool_info, meta_swap, meta_decimals, n_metacoins):
    expected = meta_decimals + [0] * (8 - n_metacoins)
    assert registry.get_decimals(meta_swap) == expected
    assert registry_pool_info.get_pool_info(meta_swap)["decimals"] == expected


def test_get_underlying_decimals(
    registry, registry_pool_info, meta_swap, meta_decimals, underlying_decimals
):
    expected = meta_decimals[:-1] + underlying_decimals
    expected += [0] * (8 - len(expected))
    assert registry.get_underlying_decimals(meta_swap) == expected
    assert registry_pool_info.get_pool_info(meta_swap)["underlying_decimals"] == expected


def test_get_pool_coins(
    registry_pool_info,
    meta_swap,
    meta_coins,
    underlying_coins,
    meta_decimals,
    underlying_decimals,
    n_metacoins,
    n_coins,
):
    coin_info = registry_pool_info.get_pool_coins(meta_swap)
    ul_trailing = 9 - n_coins - n_metacoins
    assert coin_info["coins"] == meta_coins + [ZERO_ADDRESS] * (8 - n_metacoins)
    assert (
        coin_info["underlying_coins"]
        == meta_coins[:-1] + underlying_coins + [ZERO_ADDRESS] * ul_trailing
    )
    assert coin_info["decimals"] == meta_decimals + [0] * (8 - n_metacoins)
    assert (
        coin_info["underlying_decimals"]
        == meta_decimals[:-1] + underlying_decimals + [0] * ul_trailing
    )


def test_get_rates(alice, registry, registry_pool_info, meta_swap, swap, n_metacoins):
    swap._set_virtual_price(12345678, {"from": alice})
    expected = [10 ** 18] * (n_metacoins - 1) + [12345678] + [0] * (8 - n_metacoins)
    assert registry.get_rates(meta_swap) == expected
    assert registry_pool_info.get_pool_info(meta_swap)["rates"] == expected


def test_get_balances(registry, registry_pool_info, meta_swap, n_metacoins):
    balances = [1234, 2345, 3456, 4567]
    meta_swap._set_balances(balances)

    expected = balances[:n_metacoins] + [0] * (8 - n_metacoins)
    assert registry.get_balances(meta_swap) == expected
    assert registry_pool_info.get_pool_info(meta_swap)["balances"] == expected


def test_get_underlying_balances(
    alice, registry, registry_pool_info, swap, meta_swap, n_metacoins, n_coins, lp_token
):
    balances = [1234, 2345, 3456, 4567]
    meta_swap._set_balances(balances)

    lp_token._mint_for_testing(alice, balances[n_metacoins - 1] * 5)

    underlying_balances = [5678, 6789, 7890, 8901]
    swap._set_balances(underlying_balances)

    expected = balances[: n_metacoins - 1] + [i // 5 for i in underlying_balances[:n_coins]]
    expected += [0] * (8 - len(expected))

    assert registry.get_underlying_balances(meta_swap) == expected
    assert registry_pool_info.get_pool_info(meta_swap)["underlying_balances"] == expected


def test_get_admin_balances(alice, registry, meta_swap, meta_coins):
    assert registry.get_admin_balances(meta_swap) == [0] * 8

    expected = [0] * 8
    for i, coin in enumerate(meta_coins, start=1):
        expected[i - 1] = 666 * i
        coin._mint_for_testing(meta_swap, expected[i - 1])

    assert registry.get_admin_balances(meta_swap) == expected

    meta_swap._set_balances([i // 4 for i in expected[:4]])

    expected = [i - i // 4 for i in expected]
    assert registry.get_admin_balances(meta_swap) == expected


def test_get_coin_indices(
    alice, registry, meta_swap, underlying_coins, meta_coins, n_coins, n_metacoins
):
    for i, j in itertools.combinations(range(n_metacoins), 2):
        assert registry.get_coin_indices(meta_swap, meta_coins[i], meta_coins[j]) == (i, j, False)

    coins = meta_coins[:-1] + underlying_coins
    for i, j in itertools.product(
        range(n_metacoins - 1), range(n_metacoins, n_coins + n_metacoins - 1)
    ):
        assert registry.get_coin_indices(meta_swap, coins[i], coins[j]) == (i, j, True)


@pytest.mark.once
def test_get_A(alice, registry, meta_swap):
    assert registry.get_A(meta_swap) == meta_swap.A()

    meta_swap._set_A(12345, 0, 0, 0, 0, {"from": alice})
    assert registry.get_A(meta_swap) == 12345


@pytest.mark.once
def test_get_fees(alice, registry, meta_swap):
    assert registry.get_fees(meta_swap) == [meta_swap.fee(), meta_swap.admin_fee()]

    meta_swap._set_fees_and_owner(12345, 31337, 0, 0, alice, {"from": alice})
    assert registry.get_fees(meta_swap) == [12345, 31337]


@pytest.mark.once
def test_get_virtual_price_from_lp_token(alice, registry, meta_swap, meta_lp_token):
    assert registry.get_virtual_price_from_lp_token(meta_lp_token) == 10 ** 18
    meta_swap._set_virtual_price(12345678, {"from": alice})
    assert registry.get_virtual_price_from_lp_token(meta_lp_token) == 12345678


@pytest.mark.once
def test_get_pool_from_lp_token(registry, swap, meta_swap, lp_token, meta_lp_token):
    assert registry.get_pool_from_lp_token(meta_lp_token) == meta_swap
    assert registry.get_pool_from_lp_token(lp_token) == swap


@pytest.mark.once
def test_get_lp_token(registry, swap, meta_swap, lp_token, meta_lp_token):
    assert registry.get_lp_token(meta_swap) == meta_lp_token
    assert registry.get_lp_token(swap) == lp_token


def test_coin_count_is_correct(registry, meta_coins, underlying_coins):
    coin_set = set(map(str, itertools.chain(meta_coins, underlying_coins)))

    assert registry.coin_count() == len(coin_set)


def test_get_all_swappable_coins(registry, meta_coins, underlying_coins):
    expected_coin_set = set(map(str, itertools.chain(meta_coins, underlying_coins)))
    coin_count = registry.coin_count()

    coins = set(registry.get_coin(i) for i in range(coin_count))

    assert coins == expected_coin_set


@pytest.mark.once
def test_last_updated_getter(registry, history):
    registry_txs = history.filter(receiver=registry.address)
    assert math.isclose(registry_txs[-1].timestamp, registry.last_updated())


def test_coin_swap_count(registry, meta_coins, underlying_coins):
    meta_coins = list(map(str, meta_coins))
    underlying_coins = list(map(str, underlying_coins))
    counter = Counter()

    meta_pairs = itertools.chain(*itertools.combinations(meta_coins, 2))
    underlying_pairs = itertools.chain(*itertools.combinations(underlying_coins, 2))

    meta_under_pairs = itertools.chain(
        *((meta_coin, under) for meta_coin in meta_coins[:-1] for under in underlying_coins)
    )

    counter.update(itertools.chain(meta_pairs, underlying_pairs, meta_under_pairs))

    for coin in counter.keys():
        assert registry.get_coin_swap_count(coin) == counter[coin]


def test_swap_coin_for(registry, meta_coins, underlying_coins):
    meta_coins = list(map(str, meta_coins))
    underlying_coins = list(map(str, underlying_coins))
    pairings = defaultdict(set)

    meta_pairs = itertools.combinations(meta_coins, 2)
    underlying_pairs = itertools.combinations(underlying_coins, 2)
    meta_under_pairs = (
        (meta_coin, under) for meta_coin in meta_coins[:-1] for under in underlying_coins
    )

    for coin_a, coin_b in itertools.chain(meta_pairs, underlying_pairs, meta_under_pairs):
        pairings[coin_a].add(coin_b)
        pairings[coin_b].add(coin_a)

    for coin in pairings.keys():
        coin_swap_count = len(pairings[coin])
        available_swaps = {
            registry.get_coin_swap_complement(coin, i) for i in range(coin_swap_count)
        }

        assert available_swaps == pairings[coin]


@pytest.mark.once
def test_is_metapool(registry, meta_swap):
    assert registry.is_meta(meta_swap) is True


@pytest.mark.once
def test_get_name(registry, meta_swap):
    assert registry.get_pool_name(meta_swap) == "Meta Swap"
