import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_unknown_pool(registry, pool_y):
    with brownie.reverts():
        registry.get_pool_info.call(ZERO_ADDRESS)

    with brownie.reverts():
        registry.get_pool_info.call(pool_y)



def test_fee(accounts, registry_compound, pool_compound, DAI, cUSDC):
    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['fee'] == pool_compound.fee()

    pool_compound._set_fee(31337, {'from': accounts[0]})
    assert registry_compound.get_pool_info.call(pool_compound)['fee'] == 31337


def test_A(accounts, registry_compound, pool_compound, DAI, cUSDC):
    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['A'] == pool_compound.A()

    pool_compound._set_A(31337, {'from': accounts[0]})
    assert registry_compound.get_pool_info.call(pool_compound)['A'] == 31337


def test_balance(accounts, registry_compound, pool_compound, cUSDC):
    cUSDC._mint_for_testing(1000000, {'from': accounts[0]})
    cUSDC.transfer(pool_compound, 1000000, {'from': accounts[0]})

    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['balances'] == [0, 1000000, 0, 0, 0, 0, 0, 0]


def test_underlying_balance_based_on_rate(accounts, registry_compound, pool_compound, cUSDC):
    cUSDC._mint_for_testing(1000000, {'from': accounts[0]})
    cUSDC.transfer(pool_compound, 1000000, {'from': accounts[0]})

    cUSDC._set_exchange_rate(10**18, {'from': accounts[0]})
    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['underlying_balances'] == [0, 1000000, 0, 0, 0, 0, 0, 0]

    cUSDC._set_exchange_rate(5*10**17, {'from': accounts[0]})
    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['underlying_balances'] == [0, 500000, 0, 0, 0, 0, 0, 0]


def test_actual_underlying_balance_no_effect(accounts, registry_compound, pool_compound, DAI):
    DAI._mint_for_testing(1000000, {'from': accounts[0]})
    DAI.transfer(pool_compound, 1000000, {'from': accounts[0]})

    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['underlying_balances'] == [0, 0, 0, 0, 0, 0, 0, 0]


def test_balanced_no_wrapped(accounts, registry_susd, pool_susd, DAI):
    DAI._mint_for_testing(1000000, {'from': accounts[0]})
    DAI.transfer(pool_susd, 1000000, {'from': accounts[0]})

    pool_info = registry_susd.get_pool_info.call(pool_susd)
    assert pool_info['balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]


def test_decimals(registry_compound, pool_compound):
    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['decimals'] == [8, 8, 0, 0, 0, 0, 0, 0]


def test_decimals_underlying(registry_compound, pool_compound):
    pool_info = registry_compound.get_pool_info.call(pool_compound)
    assert pool_info['underlying_decimals'] == [18, 6, 0, 0, 0, 0, 0, 0]


def test_decimals_eth(registry_eth, pool_eth):
    pool_info = registry_eth.get_pool_info.transact(pool_eth).return_value
    assert pool_info['decimals'] == [18, 6, 18, 0, 0, 0, 0, 0]


def test_balances_no_lending(accounts, registry_susd, pool_susd, DAI):
    pool_info = registry_susd.get_pool_info.call(pool_susd)
    assert pool_info['balances'] == [0, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [0, 0, 0, 0, 0, 0, 0, 0]

    DAI._mint_for_testing(1000000, {'from': accounts[0]})
    DAI.transfer(pool_susd, 1000000, {'from': accounts[0]})

    pool_info = registry_susd.get_pool_info.call(pool_susd)
    assert pool_info['balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]
