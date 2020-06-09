import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_admin_only(accounts, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.set_calculator(ZERO_ADDRESS, ZERO_ADDRESS, {'from': accounts[1]})


def test_set_calculator(accounts, registry_compound, pool_compound, calculator):
    assert registry_compound.get_calculator(pool_compound) == calculator

    registry_compound.set_calculator(pool_compound, accounts[2], {'from': accounts[0]})

    assert registry_compound.get_calculator(pool_compound) == accounts[2]


def test_set_does_not_affect_multiple(accounts, registry_all, pool_compound, pool_y, calculator):
    registry_all.set_calculator(pool_compound, accounts[2], {'from': accounts[0]})

    assert registry_all.get_calculator(pool_compound) == accounts[2]
    assert registry_all.get_calculator(pool_y) == calculator


def test_get_exchange_amounts(accounts, registry_compound, pool_compound, DAI, USDC, cDAI, cUSDC):
    DAI._mint_for_testing(10**24, {'from': accounts[0]})
    DAI.transfer(pool_compound, 10**24, {'from': accounts[0]})

    USDC._mint_for_testing(10**12, {'from': accounts[0]})
    USDC.transfer(pool_compound, 10**12, {'from': accounts[0]})

    cDAI._mint_for_testing(10**16, {'from': accounts[0]})
    cDAI.transfer(pool_compound, 10**16, {'from': accounts[0]})

    cUSDC._mint_for_testing(10**16, {'from': accounts[0]})
    cUSDC.transfer(pool_compound, 10**16, {'from': accounts[0]})
    amounts = [10**18] + [0] * 99

    # we are only verifying that these calls pass - actual values are checked in `forked` tests
    registry_compound.get_exchange_amounts(pool_compound, DAI, USDC, amounts, {'from' : accounts[0]})
    registry_compound.get_exchange_amounts(pool_compound, cDAI, cUSDC, amounts, {'from' : accounts[0]})


def test_calculator(accounts, calculator):
    expected = [89743074, 100065, 37501871, 90394938, 114182]
    actual = calculator.get_dy.call(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        False,
        0,
        1,
        [89970746, 100274, 37586976, 90624569, 114419] + [0] * 95
    )

    assert actual[:5] == expected


def test_dy_dx(accounts, calculator):
    dx = calculator.get_dx.call(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        False,
        0,
        1,
        89970746,
    )
    assert calculator.get_dy.call(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        False,
        0,
        1,
        [dx] + [0]*99
    )[0] == 89970746


def test_dx_dy(accounts, calculator):
    dy = calculator.get_dy.call(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        False,
        0,
        1,
        [89970746] + [0]*99,
    )[0]
    assert calculator.get_dx.call(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        False,
        0,
        1,
        dy
    ) == 89970746
