import brownie
import pytest
from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def registry(
    Registry, gauge_controller, alice, swap, lp_token, n_coins, is_v1, underlying_decimals,
):
    registry = Registry.deploy(gauge_controller, {"from": alice})
    registry.add_pool_without_underlying(
        swap,
        n_coins,
        lp_token,
        "0x00",
        pack_values(underlying_decimals),
        0,  # use rates
        hasattr(swap, "initial_A"),
        is_v1,
        {"from": alice},
    )
    registry.remove_pool(swap, {'from': alice})
    yield registry


@pytest.mark.itercoins("send", "recv")
def test_find_pool(registry, underlying_coins, send, recv):
    assert registry.find_pool_for_coins(underlying_coins[send], underlying_coins[recv]) == ZERO_ADDRESS


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
