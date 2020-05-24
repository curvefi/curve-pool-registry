import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_unknown_pool(registry, pool_y):
    with brownie.reverts():
        registry.get_pool_info(ZERO_ADDRESS)

    with brownie.reverts():
        registry.get_pool_info(pool_y)



def test_fee(accounts, registry_compound, pool_compound, DAI, cUSDC):
    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['fee'] == pool_compound.fee()

    pool_compound._set_fee(31337, {'from': accounts[0]})
    assert registry_compound.get_pool_info(pool_compound)['fee'] == 31337


def test_A(accounts, registry_compound, pool_compound, DAI, cUSDC):
    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['A'] == pool_compound.A()

    pool_compound._set_A(31337, {'from': accounts[0]})
    assert registry_compound.get_pool_info(pool_compound)['A'] == 31337


def test_underlying_balances(accounts, registry_compound, pool_compound, DAI):

    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['balances'] == [0, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [0, 0, 0, 0, 0, 0, 0, 0]

    DAI._mint_for_testing(1000000, {'from': accounts[0]})
    DAI.transfer(pool_compound, 1000000, {'from': accounts[0]})

    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['balances'] == [0, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]


def test_balances(accounts, registry_compound, pool_compound, cUSDC):

    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['balances'] == [0, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [0, 0, 0, 0, 0, 0, 0, 0]

    cUSDC._mint_for_testing(1000000, {'from': accounts[0]})
    cUSDC.transfer(pool_compound, 1000000, {'from': accounts[0]})

    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['balances'] == [0, 1000000, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [0, 0, 0, 0, 0, 0, 0, 0]


def test_decimals(registry_compound, pool_compound):
    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['decimals'] == [8, 8, 0, 0, 0, 0, 0, 0]


def test_decimals_underlying(registry_compound, pool_compound):
    pool_info = registry_compound.get_pool_info(pool_compound)
    assert pool_info['underlying_decimals'] == [18, 6, 0, 0, 0, 0, 0, 0]


def test_balances_no_lending(accounts, registry_susd, pool_susd, DAI):
    pool_info = registry_susd.get_pool_info(pool_susd)
    assert pool_info['balances'] == [0, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [0, 0, 0, 0, 0, 0, 0, 0]

    DAI._mint_for_testing(1000000, {'from': accounts[0]})
    DAI.transfer(pool_susd, 1000000, {'from': accounts[0]})

    pool_info = registry_susd.get_pool_info(pool_susd)
    assert pool_info['balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]
    assert pool_info['underlying_balances'] == [1000000, 0, 0, 0, 0, 0, 0, 0]
