import brownie


def test_assumption_initial_max_id(provider):
    assert provider.max_id() == 0


def test_add_and_get_info(provider, registry_pool_info, alice):
    tx = provider.add_new_id(registry_pool_info, "Pool Info", {"from": alice})

    info = provider.get_id_info(1)

    assert info["addr"] == registry_pool_info
    assert info["description"] == "Pool Info"
    assert info["version"] == 1
    assert info["is_active"] is True
    assert info["last_modified"] == tx.timestamp


def test_add_multiple(provider, registry, alice):
    last_description = "Main Registry"

    for i in range(1, 6):
        description = f"foobar{i}"
        provider.add_new_id(registry, description, {"from": alice})

        assert provider.max_id() == i
        assert provider.get_id_info(i)["description"] == description
        assert provider.get_id_info(i - 1)["description"] == last_description

        last_description = description


def test_admin_only(provider, registry, bob):
    with brownie.reverts("dev: admin-only function"):
        provider.add_new_id(registry, "", {"from": bob})


def test_contract_only(provider, alice):
    with brownie.reverts("dev: not a contract"):
        provider.add_new_id(alice, "", {"from": alice})
