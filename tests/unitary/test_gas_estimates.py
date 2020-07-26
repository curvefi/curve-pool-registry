import pytest
import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture
def set_estimates(accounts, registry_y, pool_y, DAI, USDC, USDT, yDAI, yUSDC, yUSDT):
    addr = [DAI, USDC, USDT, yDAI, yUSDC, yUSDT] + [ZERO_ADDRESS] * 4
    registry_y.set_coin_gas_estimates(addr, [10, 100, 1000, 20, 200, 2000, 0, 0, 0, 0], {'from': accounts[0]})

    addr = [pool_y] + [ZERO_ADDRESS] * 4
    registry_y.set_pool_gas_estimates(addr, [[10000, 1]] + [[0, 0]] * 4, {'from': accounts[0]})


def test_gas_estimates_underlying(accounts, registry_y, pool_y, DAI, USDC, USDT, set_estimates):
    assert registry_y.estimate_gas_used(pool_y, DAI, USDC) == 111
    assert registry_y.estimate_gas_used(pool_y, DAI, USDT) == 1011


def test_gas_estimates_wrapped(accounts, registry_y, pool_y, yDAI, yUSDC, yUSDT, set_estimates):
    assert registry_y.estimate_gas_used(pool_y, yDAI, yUSDC) == 10220
    assert registry_y.estimate_gas_used(pool_y, yDAI, yUSDT) == 12020


def test_wrapped_against_underlying(accounts, registry_y, pool_y, DAI, yUSDC, set_estimates):
    with brownie.reverts("No available market"):
        registry_y.estimate_gas_used(pool_y, DAI, yUSDC) == 10220


def test_modify_estimates(accounts, registry_y, pool_y, DAI, USDC, USDT, set_estimates):
    addr = [USDT, DAI] + ([ZERO_ADDRESS] * 8)
    registry_y.set_coin_gas_estimates(addr, [0, 9000, 0, 0, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    assert registry_y.estimate_gas_used(pool_y, DAI, USDC) == 9101

    with brownie.reverts("dev: coin value not set"):
        registry_y.estimate_gas_used(pool_y, DAI, USDT)


def test_estimator_contract(accounts, registry_y, pool_y, DAI, USDC, set_estimates):

    estimator = brownie.compile_source("""
@external
def estimate_gas_used(_pool: address, _from: address, _to: address) -> uint256:
    return 31337
    """).Vyper.deploy({'from': accounts[0]})


    assert registry_y.estimate_gas_used(pool_y, DAI, USDC) == 111

    registry_y.set_gas_estimate_contract(pool_y, estimator, {'from': accounts[0]})
    assert registry_y.estimate_gas_used(pool_y, DAI, USDC) == 31337

    registry_y.set_gas_estimate_contract(pool_y, ZERO_ADDRESS, {'from': accounts[0]})
    assert registry_y.estimate_gas_used(pool_y, DAI, USDC) == 111


def test_no_pool_value_set(accounts, registry_y, pool_y, DAI, USDC):
    addr = [DAI, USDC] + ([ZERO_ADDRESS] * 8)
    registry_y.set_coin_gas_estimates(addr, [100, 1000, 0, 0, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    with brownie.reverts("dev: pool value not set"):
        registry_y.estimate_gas_used(pool_y, DAI, USDC)


def test_no_underlying_pool_value_set(accounts, registry_y, pool_y, DAI, USDC):
    addr = [DAI, USDC] + ([ZERO_ADDRESS] * 8)
    registry_y.set_coin_gas_estimates(addr, [100, 1000, 0, 0, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    addr = [pool_y] + [ZERO_ADDRESS] * 4
    registry_y.set_pool_gas_estimates(addr, [[1, 0]] + [[0, 0]] * 4, {'from': accounts[0]})

    with brownie.reverts("dev: pool value not set"):
        registry_y.estimate_gas_used(pool_y, DAI, USDC)


def test_no_wrapped_pool_value_set(accounts, registry_y, pool_y, yDAI, yUSDC):
    addr = [yDAI, yUSDC] + ([ZERO_ADDRESS] * 8)
    registry_y.set_coin_gas_estimates(addr, [100, 1000, 0, 0, 0, 0, 0, 0, 0, 0], {'from': accounts[0]})

    addr = [pool_y] + [ZERO_ADDRESS] * 4
    registry_y.set_pool_gas_estimates(addr, [[0, 1]] + [[0, 0]] * 4, {'from': accounts[0]})

    with brownie.reverts("dev: pool value not set"):
        registry_y.estimate_gas_used(pool_y, yDAI, yUSDC)


def test_no_coin_value_set(accounts, registry_y, pool_y, DAI, USDC):
    addr = [pool_y] + [ZERO_ADDRESS] * 4
    registry_y.set_pool_gas_estimates(addr, [[1,1]] + [[0, 0]] * 4, {'from': accounts[0]})

    with brownie.reverts("dev: coin value not set"):
        registry_y.estimate_gas_used(pool_y, DAI, USDC)


def test_set_coin_admin_only(accounts, registry_y):
    with brownie.reverts("dev: admin-only function"):
        registry_y.set_coin_gas_estimates(
            [ZERO_ADDRESS] * 10,
            [0] * 10,
            {'from': accounts[1]}
        )


def test_set_pool_admin_only(accounts, registry_y):
    with brownie.reverts("dev: admin-only function"):
        registry_y.set_pool_gas_estimates(
            [ZERO_ADDRESS] * 5,
            [[0,0]] * 5,
            {'from': accounts[1]}
        )


def test_admin_only_estimator(accounts, registry_y):
    with brownie.reverts("dev: admin-only function"):
        registry_y.set_gas_estimate_contract(ZERO_ADDRESS, ZERO_ADDRESS, {'from': accounts[1]})
