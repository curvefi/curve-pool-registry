import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_set_liquidity_gauges(accounts, registry_y, pool_y, gauge_y, gauge_controller):
    gauges = [gauge_y] + [ZERO_ADDRESS] * 9
    gauge_types = [gauge_controller.gauge_types(gauge_y)] + [0] * 9
    registry_y.set_liquidity_gauges(pool_y, gauges, {'from': accounts[0]})
    assert registry_y.get_pool_gauges(pool_y) == (gauges, gauge_types)


def test_incorrect_gauge(accounts, registry_y, pool_y, gauge_susd, gauge_controller):
    gauges = [gauge_susd] + [ZERO_ADDRESS] * 9
    with brownie.reverts("dev: wrong token"):
        registry_y.set_liquidity_gauges(pool_y, gauges, {'from': accounts[0]})


def test_incorrect_multiple_gauges(accounts, registry_y, pool_y, gauge_y, gauge_susd, gauge_controller):
    gauges = [gauge_y, gauge_susd] + [ZERO_ADDRESS] * 8
    with brownie.reverts("dev: wrong token"):
        registry_y.set_liquidity_gauges(pool_y, gauges, {'from': accounts[0]})


def test_set_multiple(LiquidityGaugeMock, accounts, registry_y, pool_y, lp_y, gauge_controller):
    gauges = []
    gauge_types = []

    for i in range(10):
        gauge = LiquidityGaugeMock.deploy(lp_y, {'from': accounts[0]})
        gauge_controller._set_gauge_type(gauge, i, {'from': accounts[0]})
        gauges.append(gauge)
        gauge_types.append(i)

    registry_y.set_liquidity_gauges(pool_y, gauges, {'from': accounts[0]})
    assert registry_y.get_pool_gauges(pool_y) == (gauges, gauge_types)


def test_unset_multiple(LiquidityGaugeMock, accounts, registry_y, pool_y, lp_y, gauge_controller):
    gauges = []
    gauge_types = []

    for i in range(10):
        gauge = LiquidityGaugeMock.deploy(lp_y, {'from': accounts[0]})
        gauge_controller._set_gauge_type(gauge, i, {'from': accounts[0]})
        gauges.append(gauge)
        gauge_types.append(i)

    registry_y.set_liquidity_gauges(pool_y, gauges, {'from': accounts[0]})

    gauges = gauges[2:5] + [ZERO_ADDRESS] * 7
    gauge_types = gauge_types[2:5] + [0] * 7
    registry_y.set_liquidity_gauges(pool_y, gauges, {'from': accounts[0]})

    assert registry_y.get_pool_gauges(pool_y) == (gauges, gauge_types)
