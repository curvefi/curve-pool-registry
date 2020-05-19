import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_gas_estimates(accounts, registry, pool_susd, DAI, USDC, sUSD):
    addr = [pool_susd, DAI, USDC, sUSD] + ([ZERO_ADDRESS] * 6)
    registry.set_gas_estimates(addr, [1, 10, 100, 1000, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    assert registry.estimate_gas_used(pool_susd, DAI, USDC) == 111
    assert registry.estimate_gas_used(pool_susd, DAI, sUSD) == 1011


def test_modify_estimates(accounts, registry, pool_susd, DAI, USDC, sUSD):
    addr = [pool_susd, DAI, USDC, sUSD] + ([ZERO_ADDRESS] * 6)
    registry.set_gas_estimates(addr, [1, 10, 100, 1000, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    addr = [sUSD, DAI] + ([ZERO_ADDRESS] * 8)
    registry.set_gas_estimates(addr, [0, 9000, 0, 0, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    assert registry.estimate_gas_used(pool_susd, DAI, USDC) == 9101

    with brownie.reverts("dev: value not set"):
        registry.estimate_gas_used(pool_susd, DAI, sUSD)


def test_no_value_set(registry, pool_susd, DAI, USDC):
    with brownie.reverts("dev: value not set"):
        registry.estimate_gas_used(pool_susd, DAI, USDC)


def test_admin_only(accounts, registry):
    with brownie.reverts("dev: admin-only function"):
        registry.set_gas_estimates(
            [ZERO_ADDRESS] * 10,
            [0] * 10,
            {'from': accounts[1]}
        )
