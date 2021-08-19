import brownie
from brownie import ETH_ADDRESS


def test_newly_deployed_gauge_auto_registers(alice, gauge_registry, mock_factory):
    tx = mock_factory.deploy({"from": alice})

    assert gauge_registry.gauge_count() == 1
    assert gauge_registry.gauge_list(0) == tx.new_contracts[0]
    assert gauge_registry.gauge_version(tx.new_contracts[0]) == 1
    assert gauge_registry.pool_address(tx.new_contracts[0]) == ETH_ADDRESS


def test_admin_can_register_a_gauge(alice, gauge_registry):
    gauge_registry.register(ETH_ADDRESS, ETH_ADDRESS, 42, {"from": alice})

    assert gauge_registry.gauge_count() == 1
    assert gauge_registry.gauge_list(0) == ETH_ADDRESS
    assert gauge_registry.gauge_version(ETH_ADDRESS) == 42
    assert gauge_registry.pool_address(ETH_ADDRESS) == ETH_ADDRESS


def test_guarded_register(bob, gauge_registry):
    with brownie.reverts():
        gauge_registry.register(ETH_ADDRESS, ETH_ADDRESS, 42, {"from": bob})
