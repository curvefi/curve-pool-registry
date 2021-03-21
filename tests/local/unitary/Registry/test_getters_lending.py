import itertools
import math
from collections import Counter, defaultdict

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
        "Lending Swap",
        {"from": alice},
    )
    provider.set_address(0, registry, {"from": alice})
    yield registry


@pytest.mark.itercoins("send", "recv")
def test_find_pool(registry, lending_swap, wrapped_coins, send, recv):
    send = wrapped_coins[send]
    recv = wrapped_coins[recv]
    assert registry.find_pool_for_coins(send, recv) == lending_swap


@pytest.mark.itercoins("send", "recv")
def test_find_pool_underlying(registry, lending_swap, underlying_coins, send, recv):
    send = underlying_coins[send]
    recv = underlying_coins[recv]
    assert registry.find_pool_for_coins(send, recv) == lending_swap


@pytest.mark.itercoins("idx")
def test_find_pool_not_exists(registry, lending_swap, wrapped_coins, underlying_coins, idx):
    assert registry.find_pool_for_coins(wrapped_coins[idx], wrapped_coins[idx]) == ZERO_ADDRESS
    assert (
        registry.find_pool_for_coins(underlying_coins[idx], underlying_coins[idx]) == ZERO_ADDRESS
    )
    assert registry.find_pool_for_coins(wrapped_coins[idx], underlying_coins[idx]) == ZERO_ADDRESS


def test_get_n_coins(registry, lending_swap, n_coins):
    assert registry.get_n_coins(lending_swap) == [n_coins, n_coins]


def test_get_coins(registry, lending_swap, wrapped_coins, n_coins):
    assert registry.get_coins(lending_swap) == wrapped_coins + [ZERO_ADDRESS] * (8 - n_coins)


def test_get_underlying_coins(registry, lending_swap, underlying_coins, n_coins):
    assert registry.get_underlying_coins(lending_swap) == underlying_coins + [ZERO_ADDRESS] * (
        8 - n_coins
    )


def test_get_decimals(registry, registry_pool_info, lending_swap, wrapped_decimals, n_coins):
    expected = wrapped_decimals + [0] * (8 - n_coins)
    assert registry.get_decimals(lending_swap) == expected
    assert registry_pool_info.get_pool_info(lending_swap)["decimals"] == expected


def test_get_underlying_decimals(
    registry, registry_pool_info, lending_swap, underlying_decimals, n_coins
):
    expected = underlying_decimals + [0] * (8 - n_coins)
    assert registry.get_underlying_decimals(lending_swap) == expected
    assert registry_pool_info.get_pool_info(lending_swap)["underlying_decimals"] == expected


def test_get_pool_coins(
    registry_pool_info,
    lending_swap,
    underlying_coins,
    wrapped_coins,
    underlying_decimals,
    wrapped_decimals,
    n_coins,
):
    coin_info = registry_pool_info.get_pool_coins(lending_swap)
    assert coin_info["coins"] == wrapped_coins + [ZERO_ADDRESS] * (8 - n_coins)
    assert coin_info["underlying_coins"] == underlying_coins + [ZERO_ADDRESS] * (8 - n_coins)
    assert coin_info["decimals"] == wrapped_decimals + [0] * (8 - n_coins)
    assert coin_info["underlying_decimals"] == underlying_decimals + [0] * (8 - n_coins)


def test_get_rates(registry, registry_pool_info, lending_swap, wrapped_coins):
    rates = []
    for i, coin in enumerate(wrapped_coins, start=1):
        if hasattr(coin, "_set_exchange_rate"):
            rates.append(int(10 ** 18 * ((100 + i) / 100)))
            coin._set_exchange_rate(rates[-1])
        else:
            rates.append(10 ** 18)
    rates += [0] * (8 - len(rates))

    assert registry.get_rates(lending_swap) == rates
    assert registry_pool_info.get_pool_info(lending_swap)["rates"] == rates


def test_get_balances(registry, registry_pool_info, lending_swap, n_coins):
    balances = [1234, 2345, 3456, 4567]
    lending_swap._set_balances(balances)

    expected = balances[:n_coins] + [0] * (8 - n_coins)
    assert registry.get_balances(lending_swap) == expected
    assert registry_pool_info.get_pool_info(lending_swap)["balances"] == expected


def test_get_underlying_balances(
    registry, registry_pool_info, lending_swap, wrapped_coins, underlying_decimals, n_coins
):
    balances = [1234, 2345, 3456, 4567]
    lending_swap._set_balances(balances)

    rates = []
    for i, coin in enumerate(wrapped_coins, start=1):
        if hasattr(coin, "_set_exchange_rate"):
            rates.append(int(10 ** 18 * ((100 + i) / 100)))
            coin._set_exchange_rate(rates[-1])
        else:
            rates.append(10 ** 18)
    rates += [0] * (8 - len(rates))

    balances = [i * r // 10 ** d for i, r, d in zip(balances, rates, underlying_decimals)]
    expected = balances[:n_coins] + [0] * (8 - n_coins)

    assert registry.get_underlying_balances(lending_swap) == expected
    assert registry_pool_info.get_pool_info(lending_swap)["underlying_balances"] == expected


def test_get_admin_balances(alice, registry, lending_swap, wrapped_coins, n_coins):
    assert registry.get_admin_balances(lending_swap) == [0] * 8

    expected = [0] * 8
    for i, coin in enumerate(wrapped_coins, start=1):
        expected[i - 1] = 666 * i
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            alice.transfer(lending_swap, expected[i - 1])
        else:
            coin._mint_for_testing(lending_swap, expected[i - 1])

    assert registry.get_admin_balances(lending_swap) == expected

    lending_swap._set_balances([i // 4 for i in expected[:4]])

    expected = [i - i // 4 for i in expected]
    assert registry.get_admin_balances(lending_swap) == expected


@pytest.mark.itercoins("send", "recv")
def test_get_coin_indices(
    alice, registry, lending_swap, wrapped_coins, underlying_coins, send, recv
):
    assert registry.get_coin_indices(lending_swap, wrapped_coins[send], wrapped_coins[recv]) == (
        send,
        recv,
        False,
    )
    assert registry.get_coin_indices(
        lending_swap, underlying_coins[send], underlying_coins[recv]
    ) == (send, recv, True)


@pytest.mark.once
def test_get_A(alice, registry, registry_pool_info, lending_swap):
    assert registry.get_A(lending_swap) == lending_swap.A()

    lending_swap._set_A(12345, 0, 0, 0, 0, {"from": alice})
    assert registry.get_A(lending_swap) == 12345
    assert registry_pool_info.get_pool_info(lending_swap)["params"]["A"] == 12345


@pytest.mark.once
def test_get_fees(alice, registry, registry_pool_info, lending_swap):
    assert registry.get_fees(lending_swap) == [lending_swap.fee(), lending_swap.admin_fee()]

    lending_swap._set_fees_and_owner(12345, 31337, 42, 69420, alice, {"from": alice})
    assert registry.get_fees(lending_swap) == [12345, 31337]

    pool_info = registry_pool_info.get_pool_info(lending_swap)["params"]
    assert pool_info["fee"] == 12345
    assert pool_info["admin_fee"] == 31337
    assert pool_info["future_fee"] == 42
    assert pool_info["future_admin_fee"] == 69420


@pytest.mark.once
def test_get_virtual_price_from_lp_token(alice, registry, lending_swap, lp_token):
    assert registry.get_virtual_price_from_lp_token(lp_token) == 10 ** 18
    lending_swap._set_virtual_price(12345678, {"from": alice})
    assert registry.get_virtual_price_from_lp_token(lp_token) == 12345678


@pytest.mark.once
def test_get_pool_from_lp_token(registry, lending_swap, lp_token):
    assert registry.get_pool_from_lp_token(lp_token) == lending_swap


@pytest.mark.once
def test_get_lp_token(registry, lending_swap, lp_token):
    assert registry.get_lp_token(lending_swap) == lp_token


def test_coin_count_is_correct(registry, wrapped_coins, underlying_coins):
    coin_set = set(map(str, itertools.chain(wrapped_coins, underlying_coins)))

    assert registry.coin_count() == len(coin_set)


def test_get_all_swappable_coins(registry, wrapped_coins, underlying_coins):
    expected_coin_set = set(map(str, itertools.chain(wrapped_coins, underlying_coins)))
    coin_count = registry.coin_count()

    coins = set(registry.get_coin(i) for i in range(coin_count))

    assert coins == expected_coin_set


@pytest.mark.once
def test_last_updated_getter(registry, history):
    registry_txs = history.filter(receiver=registry.address)
    assert math.isclose(registry_txs[-1].timestamp, registry.last_updated())


def test_coin_swap_count(registry, wrapped_coins, underlying_coins):
    wrapped_coins = list(map(str, wrapped_coins))
    underlying_coins = list(map(str, underlying_coins))

    counter = Counter()

    wrapped_pairs = itertools.chain(*itertools.combinations(wrapped_coins, 2))
    underlying_pairs = itertools.chain(*itertools.combinations(underlying_coins, 2))

    counter.update(itertools.chain(wrapped_pairs, underlying_pairs))

    for coin in counter.keys():
        assert registry.get_coin_swap_count(coin) == counter[coin]


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
        coin_swap_count = registry.get_coin_swap_count(coin)
        available_swaps = {
            registry.get_coin_swap_complement(coin, i) for i in range(coin_swap_count)
        }

        assert available_swaps == pairings[coin]


@pytest.mark.once
def test_is_metapool(registry, lending_swap):
    assert registry.is_meta(lending_swap) is False


@pytest.mark.once
def test_get_name(registry, lending_swap):
    assert registry.get_pool_name(lending_swap) == "Lending Swap"
