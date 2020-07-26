import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_admin_is_deployer(Registry, accounts):
    registry = Registry.deploy({'from': accounts[0]})
    assert registry.admin() == accounts[0]

    registry = Registry.deploy({'from': accounts[1]})
    assert registry.admin() == accounts[1]


def test_transfer_ownership(accounts, chain, registry):
    registry.commit_transfer_ownership(accounts[2], {'from': accounts[0]})
    assert registry.admin() == accounts[0]

    chain.sleep(3*86400)
    registry.apply_transfer_ownership({'from': accounts[0]})

    assert registry.admin() == accounts[2]


def test_time_delay(accounts, chain, registry):
    registry.commit_transfer_ownership(accounts[2], {'from': accounts[0]})

    # immediate
    with brownie.reverts("dev: now < deadline"):
        registry.apply_transfer_ownership({'from': accounts[0]})

    chain.sleep(86400)
    with brownie.reverts("dev: now < deadline"):
        registry.apply_transfer_ownership({'from': accounts[0]})

    chain.sleep(86400)
    with brownie.reverts("dev: now < deadline"):
        registry.apply_transfer_ownership({'from': accounts[0]})

    chain.sleep(86400)
    registry.apply_transfer_ownership({'from': accounts[0]})


def test_revert_transfer(accounts, chain, registry):
    registry.commit_transfer_ownership(accounts[2], {'from': accounts[0]})

    chain.sleep(3*86400)
    registry.revert_transfer_ownership({'from': accounts[0]})

    with brownie.reverts("dev: transfer not active"):
        registry.apply_transfer_ownership({'from': accounts[0]})


def test_commit_already_pending(accounts, registry):
    registry.commit_transfer_ownership(accounts[2], {'from': accounts[0]})

    with brownie.reverts("dev: transfer already active"):
        registry.commit_transfer_ownership(accounts[2], {'from': accounts[0]})


def test_commit_admin_only(accounts, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.commit_transfer_ownership(accounts[2], {'from': accounts[1]})

def test_apply_admin_only(accounts, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.apply_transfer_ownership({'from': accounts[1]})

def test_revert_admin_only(accounts, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.revert_transfer_ownership({'from': accounts[1]})


def test_transfer_twice(accounts, chain, registry):
    registry.commit_transfer_ownership(accounts[2], {'from': accounts[0]})

    chain.sleep(3*86400)
    registry.apply_transfer_ownership({'from': accounts[0]})
    registry.commit_transfer_ownership(accounts[1], {'from': accounts[2]})

    chain.sleep(3*86400)
    registry.apply_transfer_ownership({'from': accounts[2]})
    assert registry.admin() == accounts[1]
