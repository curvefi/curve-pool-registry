import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def setup(provider, registry_pool_info, registry_swap, alice):
    provider.add_new_id(registry_pool_info, "pool info", {"from": alice})
    provider.add_new_id(registry_swap, "swap", {"from": alice})


def test_initial_id_info_1(provider, registry_pool_info):
    info = provider.get_id_info(1)

    assert info["description"] == "pool info"
    assert info["version"] == 1
    assert info["is_active"] is True
    assert info["addr"] == registry_pool_info


def test_initial_id_info_2(provider, registry_swap):
    info = provider.get_id_info(2)

    assert info["description"] == "swap"
    assert info["version"] == 1
    assert info["is_active"] is True
    assert info["addr"] == registry_swap


def test_set(provider, registry_swap, registry, alice):
    tx = provider.set_address(1, registry_swap, {"from": alice})
    info = provider.get_id_info(1)

    assert info["description"] == "pool info"
    assert info["version"] == 2
    assert info["is_active"] is True
    assert info["last_modified"] == tx.timestamp
    assert info["addr"] == registry_swap


def test_unset(provider, registry, alice):
    tx = provider.unset_address(1, {"from": alice})
    info = provider.get_id_info(1)

    assert info["description"] == "pool info"
    assert info["version"] == 1
    assert info["is_active"] is False
    assert info["last_modified"] == tx.timestamp
    assert info["addr"] == ZERO_ADDRESS


def test_registry_not_affected(provider, registry, registry_swap, alice):
    provider.set_address(1, registry_swap, {"from": alice})
    provider.set_address(2, registry_swap, {"from": alice})

    assert provider.get_registry() == registry


def test_set_admin_only(provider, registry, bob):
    with brownie.reverts("dev: admin-only function"):
        provider.set_address(1, registry, {"from": bob})


def test_unset_admin_only(provider, bob):
    with brownie.reverts("dev: admin-only function"):
        provider.unset_address(1, {"from": bob})


def test_set_contract_only(provider, alice):
    with brownie.reverts("dev: not a contract"):
        provider.set_address(1, alice, {"from": alice})


def test_set_beyond_max_id(provider, registry, alice):
    max_id = provider.max_id()
    with brownie.reverts("dev: id does not exist"):
        provider.set_address(max_id + 1, registry, {"from": alice})


def test_unset_beyond_max_id(provider, alice):
    max_id = provider.max_id()
    with brownie.reverts("dev: not active"):
        provider.unset_address(max_id + 1, {"from": alice})


def test_unset_inactive(provider, alice):
    max_id = provider.max_id()
    provider.unset_address(max_id, {"from": alice})

    with brownie.reverts("dev: not active"):
        provider.unset_address(max_id, {"from": alice})
