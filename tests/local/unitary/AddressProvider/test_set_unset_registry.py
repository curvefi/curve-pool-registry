from brownie import ZERO_ADDRESS


def test_assumptions_registry_is_unset(provider):
    assert provider.get_registry() == ZERO_ADDRESS
    assert provider.get_address(0) == ZERO_ADDRESS


def test_initial_id_info(provider):
    info = provider.get_id_info(0)

    assert info["description"] == "Main Registry"
    assert info["version"] == 0
    assert info["is_active"] is False


def test_set_registry(provider, registry, alice):
    provider.set_address(0, registry, {"from": alice})

    assert provider.get_registry() == registry
    assert provider.get_address(0) == registry


def test_unset_registry(provider, registry, alice):
    provider.set_address(0, registry, {"from": alice})
    provider.unset_address(0, {"from": alice})

    assert provider.get_registry() == ZERO_ADDRESS
    assert provider.get_address(0) == ZERO_ADDRESS


def test_unset_and_set_again(provider, registry, alice):
    provider.set_address(0, registry, {"from": alice})
    provider.unset_address(0, {"from": alice})
    provider.set_address(0, registry, {"from": alice})

    assert provider.get_registry() == registry
    assert provider.get_address(0) == registry
