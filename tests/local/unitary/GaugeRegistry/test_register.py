from brownie import ETH_ADDRESS


def test_newly_deployed_gauge_auto_registers(alice, gauge_registry, mock_factory):
    tx = mock_factory.deploy({"from": alice})

    assert gauge_registry.gauge_count() == 1
    assert gauge_registry.gauge_list(0) == tx.new_contracts[0]
    assert gauge_registry.gauge_version(tx.new_contracts[0]) == 1
    assert gauge_registry.pool_address(tx.new_contracts[0]) == ETH_ADDRESS
