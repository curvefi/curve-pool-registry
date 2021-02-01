import brownie


def test_set_admin_on_deployment(AddressProvider, alice, bob):
    provider = AddressProvider.deploy(alice, {"from": alice})
    assert provider.admin() == alice

    provider = AddressProvider.deploy(bob, {"from": alice})
    assert provider.admin() == bob


def test_transfer_ownership(alice, bob, chain, provider):
    provider.commit_transfer_ownership(bob, {"from": alice})
    assert provider.admin() == alice

    chain.sleep(3 * 86400)
    provider.apply_transfer_ownership({"from": alice})

    assert provider.admin() == bob


def test_time_delay(alice, bob, chain, provider):
    provider.commit_transfer_ownership(bob, {"from": alice})

    # immediate
    with brownie.reverts("dev: now < deadline"):
        provider.apply_transfer_ownership({"from": alice})

    chain.sleep(86400)
    with brownie.reverts("dev: now < deadline"):
        provider.apply_transfer_ownership({"from": alice})

    chain.sleep(86400)
    with brownie.reverts("dev: now < deadline"):
        provider.apply_transfer_ownership({"from": alice})

    chain.sleep(86400)
    provider.apply_transfer_ownership({"from": alice})


def test_revert_transfer(alice, bob, chain, provider):
    provider.commit_transfer_ownership(bob, {"from": alice})

    chain.sleep(3 * 86400)
    provider.revert_transfer_ownership({"from": alice})

    with brownie.reverts("dev: transfer not active"):
        provider.apply_transfer_ownership({"from": alice})


def test_commit_already_pending(alice, bob, provider):
    provider.commit_transfer_ownership(bob, {"from": alice})

    with brownie.reverts("dev: transfer already active"):
        provider.commit_transfer_ownership(bob, {"from": alice})


def test_commit_admin_only(bob, provider):
    with brownie.reverts("dev: admin-only function"):
        provider.commit_transfer_ownership(bob, {"from": bob})


def test_apply_admin_only(bob, provider):
    with brownie.reverts("dev: admin-only function"):
        provider.apply_transfer_ownership({"from": bob})


def test_revert_admin_only(bob, provider):
    with brownie.reverts("dev: admin-only function"):
        provider.revert_transfer_ownership({"from": bob})


def test_transfer_twice(alice, bob, chain, provider):
    provider.commit_transfer_ownership(bob, {"from": alice})

    chain.sleep(3 * 86400)
    provider.apply_transfer_ownership({"from": alice})
    provider.commit_transfer_ownership(bob, {"from": bob})

    chain.sleep(3 * 86400)
    provider.apply_transfer_ownership({"from": bob})
    assert provider.admin() == bob
