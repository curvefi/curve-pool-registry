import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_admin_is_deployer(Registry, alice, bob, gauge_controller):
    registry = Registry.deploy(gauge_controller, {'from': alice})
    assert registry.admin() == alice

    registry = Registry.deploy(gauge_controller, {'from': bob})
    assert registry.admin() == bob


def test_transfer_ownership(alice, bob, chain, registry):
    registry.commit_transfer_ownership(bob, {'from': alice})
    assert registry.admin() == alice

    chain.sleep(3*86400)
    registry.apply_transfer_ownership({'from': alice})

    assert registry.admin() == bob


def test_time_delay(alice, bob, chain, registry):
    registry.commit_transfer_ownership(bob, {'from': alice})

    # immediate
    with brownie.reverts("dev: now < deadline"):
        registry.apply_transfer_ownership({'from': alice})

    chain.sleep(86400)
    with brownie.reverts("dev: now < deadline"):
        registry.apply_transfer_ownership({'from': alice})

    chain.sleep(86400)
    with brownie.reverts("dev: now < deadline"):
        registry.apply_transfer_ownership({'from': alice})

    chain.sleep(86400)
    registry.apply_transfer_ownership({'from': alice})


def test_revert_transfer(alice, bob, chain, registry):
    registry.commit_transfer_ownership(bob, {'from': alice})

    chain.sleep(3*86400)
    registry.revert_transfer_ownership({'from': alice})

    with brownie.reverts("dev: transfer not active"):
        registry.apply_transfer_ownership({'from': alice})


def test_commit_already_pending(alice, bob, registry):
    registry.commit_transfer_ownership(bob, {'from': alice})

    with brownie.reverts("dev: transfer already active"):
        registry.commit_transfer_ownership(bob, {'from': alice})


def test_commit_admin_only(bob, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.commit_transfer_ownership(bob, {'from': bob})


def test_apply_admin_only(bob, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.apply_transfer_ownership({'from': bob})


def test_revert_admin_only(bob, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.revert_transfer_ownership({'from': bob})


def test_transfer_twice(alice, bob, chain, registry):
    registry.commit_transfer_ownership(bob, {'from': alice})

    chain.sleep(3*86400)
    registry.apply_transfer_ownership({'from': alice})
    registry.commit_transfer_ownership(bob, {'from': bob})

    chain.sleep(3*86400)
    registry.apply_transfer_ownership({'from': bob})
    assert registry.admin() == bob
