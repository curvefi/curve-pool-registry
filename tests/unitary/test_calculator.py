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
    amounts = [10**18] + [0] * 49#, 20000000, 50000000, 1000000000, 1000000] + [0] * 45

    # we are only verifying that these calls pass - actual values are checked in `forked` tests
    registry_compound.get_exchange_amounts(pool_compound, DAI, USDC, amounts, {'from' : accounts[0]})
    registry_compound.get_exchange_amounts(pool_compound, cDAI, cUSDC, amounts, {'from' : accounts[0]})


def test_calculator(accounts, calculator):
    expected = (89743074, 100065, 37501871, 90394938, 114182, 99825, 112638, 93543613, 99957, 100133, 99945, 139004, 20938989, 137601, 100048, 113641, 128660, 99796, 129842, 79202864, 45423162, 139685, 33579518, 99818, 149986, 165496, 67122989, 99858, 143874, 143222, 99795, 99798, 99944, 99793, 99794, 146144, 106527, 59661555, 99911, 100142, 73100615, 114460, 145521, 99819, 99810, 99919, 99882, 147311, 99915, 99913)

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
        (89970746, 100274, 37586976, 90624569, 114419, 100032, 112873, 93782770, 100165, 100342, 100152, 139293, 20984754, 137888, 100257, 113878, 128928, 100003, 130112, 79399483, 45528070, 139975, 33655055, 100025, 150299, 165841, 67285451, 100065, 144173, 143520, 100002, 100005, 100151, 100000, 100001, 146448, 106749, 59803679, 100118, 100351, 73279789, 114698, 145824, 100026, 100017, 100126, 100089, 147617, 100122, 100120)
    )


    assert actual == expected
