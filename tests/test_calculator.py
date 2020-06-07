import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_admin_only(accounts, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.set_calculator(ZERO_ADDRESS, ZERO_ADDRESS, {'from': accounts[1]})


def test_set_calculator(accounts, registry):
    assert registry.get_calculator(accounts[1]) == ZERO_ADDRESS

    registry.set_calculator(accounts[1], accounts[2], {'from': accounts[0]})

    assert registry.get_calculator(accounts[1]) == accounts[2]
