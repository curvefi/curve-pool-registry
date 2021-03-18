import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

pytestmark = pytest.mark.once


@pytest.fixture(scope="module", autouse=True)
def registry(Registry, provider, gauge_controller, alice, swap, lp_token, n_coins, is_v1):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
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


def test_set_liquidity_gauges(alice, registry, gauge_controller, liquidity_gauge, swap, lp_token):
    gauges = [liquidity_gauge] + [ZERO_ADDRESS] * 9
    gauge_types = [gauge_controller.gauge_types(liquidity_gauge)] + [0] * 9
    registry.set_liquidity_gauges(swap, gauges, {"from": alice})
    assert registry.get_gauges(swap) == (gauges, gauge_types)


def test_incorrect_gauge(LiquidityGaugeMock, alice, registry, gauge_controller, swap):
    gauge = LiquidityGaugeMock.deploy(swap, {"from": alice})
    gauges = [gauge] + [ZERO_ADDRESS] * 9
    with brownie.reverts("dev: wrong token"):
        registry.set_liquidity_gauges(swap, gauges, {"from": alice})


def test_incorrect_gauge_multiple(
    LiquidityGaugeMock, alice, registry, gauge_controller, liquidity_gauge, swap
):
    gauge = LiquidityGaugeMock.deploy(swap, {"from": alice})
    gauges = [liquidity_gauge, gauge] + [ZERO_ADDRESS] * 8
    with brownie.reverts("dev: wrong token"):
        registry.set_liquidity_gauges(swap, gauges, {"from": alice})


def test_set_multiple(LiquidityGaugeMock, alice, registry, swap, lp_token, gauge_controller):
    gauges = []
    gauge_types = []

    for i in range(10):
        gauge = LiquidityGaugeMock.deploy(lp_token, {"from": alice})
        gauge_controller._set_gauge_type(gauge, i, {"from": alice})
        gauges.append(gauge)
        gauge_types.append(i)

    registry.set_liquidity_gauges(swap, gauges, {"from": alice})
    assert registry.get_gauges(swap) == (gauges, gauge_types)


def test_unset_multiple(LiquidityGaugeMock, alice, registry, swap, lp_token, gauge_controller):
    gauges = []
    gauge_types = []

    for i in range(10):
        gauge = LiquidityGaugeMock.deploy(lp_token, {"from": alice})
        gauge_controller._set_gauge_type(gauge, i, {"from": alice})
        gauges.append(gauge)
        gauge_types.append(i)

    registry.set_liquidity_gauges(swap, gauges, {"from": alice})

    gauges = gauges[2:5] + [ZERO_ADDRESS] * 7
    gauge_types = gauge_types[2:5] + [0] * 7
    registry.set_liquidity_gauges(swap, gauges, {"from": alice})

    assert registry.get_gauges(swap) == (gauges, gauge_types)
