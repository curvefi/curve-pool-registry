import itertools as it
import math
from collections import Counter, defaultdict

import pytest

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def registry(
    Registry, provider, gauge_controller, alice, swap, lp_token, n_coins, is_v1, underlying_decimals
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
        "Base Swap",
        {"from": alice},
    )
    provider.set_address(0, registry, {"from": alice})
    yield registry


@pytest.mark.itercoins("send", "recv")
def test_find_pool(registry, swap, underlying_coins, send, recv):
    assert registry.find_pool_for_coins(underlying_coins[send], underlying_coins[recv]) == swap


@pytest.mark.itercoins("idx")
def test_find_pool_not_exists(registry, swap, underlying_coins, idx):
    assert (
        registry.find_pool_for_coins(underlying_coins[idx], underlying_coins[idx]) == ZERO_ADDRESS
    )


def test_get_n_coins(registry, swap, n_coins):
    assert registry.get_n_coins(swap) == [n_coins, n_coins]


def test_get_coins(registry, swap, underlying_coins, n_coins):
    expected = underlying_coins + [ZERO_ADDRESS] * (8 - n_coins)
    assert registry.get_coins(swap) == expected
    assert registry.get_underlying_coins(swap) == expected


def test_get_decimals(registry, registry_pool_info, swap, underlying_decimals, n_coins):
    expected = underlying_decimals + [0] * (8 - n_coins)
    assert registry.get_decimals(swap) == expected
    assert registry.get_underlying_decimals(swap) == expected

    pool_info = registry_pool_info.get_pool_info(swap)
    assert pool_info["decimals"] == expected
    assert pool_info["underlying_decimals"] == expected


def test_get_pool_coins(registry_pool_info, swap, underlying_coins, underlying_decimals, n_coins):
    coin_info = registry_pool_info.get_pool_coins(swap)
    assert coin_info["coins"] == underlying_coins + [ZERO_ADDRESS] * (8 - n_coins)
    assert coin_info["underlying_coins"] == underlying_coins + [ZERO_ADDRESS] * (8 - n_coins)
    assert coin_info["decimals"] == underlying_decimals + [0] * (8 - n_coins)
    assert coin_info["underlying_decimals"] == underlying_decimals + [0] * (8 - n_coins)


def test_get_rates(registry, registry_pool_info, swap, n_coins):
    expected = [10 ** 18] * n_coins + [0] * (8 - n_coins)
    assert registry.get_rates(swap) == expected
    assert registry_pool_info.get_pool_info(swap)["rates"] == expected


def test_get_balances(registry, registry_pool_info, swap, n_coins):
    balances = [1234, 2345, 3456, 4567]
    swap._set_balances(balances)

    expected = balances[:n_coins] + [0] * (8 - n_coins)
    assert registry.get_balances(swap) == expected
    assert registry.get_underlying_balances(swap) == expected

    pool_info = registry_pool_info.get_pool_info(swap)
    assert pool_info["balances"] == expected
    assert pool_info["underlying_balances"] == expected


def test_get_admin_balances(alice, registry, swap, underlying_coins, n_coins):
    assert registry.get_admin_balances(swap) == [0] * 8

    expected = [0] * 8
    for i, coin in enumerate(underlying_coins, start=1):
        expected[i - 1] = 666 * i
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            alice.transfer(swap, expected[i - 1])
        else:
            coin._mint_for_testing(swap, expected[i - 1])

    assert registry.get_admin_balances(swap) == expected

    swap._set_balances([i // 4 for i in expected[:4]])

    expected = [i - i // 4 for i in expected]
    assert registry.get_admin_balances(swap) == expected


@pytest.mark.itercoins("send", "recv")
def test_get_coin_indices(alice, registry, swap, underlying_coins, send, recv):
    assert registry.get_coin_indices(swap, underlying_coins[send], underlying_coins[recv]) == (
        send,
        recv,
        False,
    )


@pytest.mark.once
def test_get_A(alice, registry, swap):
    assert registry.get_A(swap) == swap.A()

    swap._set_A(12345, 0, 0, 0, 0, {"from": alice})
    assert registry.get_A(swap) == 12345


@pytest.mark.once
def test_get_fees(alice, registry, swap):
    assert registry.get_fees(swap) == [swap.fee(), swap.admin_fee()]

    swap._set_fees_and_owner(12345, 31337, 0, 0, alice, {"from": alice})
    assert registry.get_fees(swap) == [12345, 31337]


@pytest.mark.once
def test_get_virtual_price_from_lp_token(alice, registry, swap, lp_token):
    assert registry.get_virtual_price_from_lp_token(lp_token) == 10 ** 18
    swap._set_virtual_price(12345678, {"from": alice})
    assert registry.get_virtual_price_from_lp_token(lp_token) == 12345678


@pytest.mark.once
def test_get_pool_from_lp_token(registry, swap, lp_token):
    assert registry.get_pool_from_lp_token(lp_token) == swap


@pytest.mark.once
def test_get_lp_token(registry, swap, lp_token):
    assert registry.get_lp_token(swap) == lp_token


def test_coin_count_is_correct(registry, underlying_coins):
    coin_set = set(map(str, underlying_coins))

    assert registry.coin_count() == len(coin_set)


def test_get_all_swappable_coins(registry, underlying_coins):
    expected_coin_set = set(map(str, underlying_coins))
    coin_count = registry.coin_count()

    coins = set(registry.get_coin(i) for i in range(coin_count))

    assert coins == expected_coin_set


@pytest.mark.once
def test_last_updated_getter(registry, history):
    registry_txs = history.filter(receiver=registry.address)
    assert math.isclose(registry_txs[-1].timestamp, registry.last_updated())


def test_coin_swap_count(registry, underlying_coins):
    underlying_coins = set(map(str, underlying_coins))
    pairings = it.combinations(underlying_coins, 2)
    counts = Counter(it.chain(*pairings))

    for coin in underlying_coins:
        assert registry.get_coin_swap_count(coin) == counts[coin]


def test_swap_coin_for(registry, underlying_coins):
    underlying_coins = set(map(str, underlying_coins))
    pairings = it.combinations(underlying_coins, 2)
    swaps = defaultdict(set)

    for coina, coinb in pairings:
        swaps[coina].add(coinb)
        swaps[coinb].add(coina)

    for coin in underlying_coins:
        coin_swap_count = registry.get_coin_swap_count(coin)
        swap_coins = {registry.get_coin_swap_complement(coin, i) for i in range(coin_swap_count)}

        assert swap_coins == swaps[coin]


@pytest.mark.once
def test_is_metapool(registry, swap):
    assert registry.is_meta(swap) is False


@pytest.mark.once
def test_get_name(registry, swap):
    assert registry.get_pool_name(swap) == "Base Swap"
