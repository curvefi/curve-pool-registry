import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# we are using transactions here to be able to compare gas costs

def test_find_coin_pool(registry_compound, cDAI, cUSDC, pool_compound):
    assert registry_compound.find_pool_for_coins.transact(cDAI, cUSDC).return_value == pool_compound
    assert registry_compound.find_pool_for_coins.transact(cUSDC, cDAI).return_value == pool_compound


def test_find_underlying_coin_pool(registry_compound, DAI, USDC, pool_compound):
    assert registry_compound.find_pool_for_coins.transact(DAI, USDC).return_value == pool_compound
    assert registry_compound.find_pool_for_coins.transact(USDC, DAI).return_value == pool_compound


def test_no_pool_coin_underlying_mismatch(registry_compound, cDAI, USDC, pool_compound):
    assert registry_compound.find_pool_for_coins.transact(cDAI, USDC).return_value == ZERO_ADDRESS
    assert registry_compound.find_pool_for_coins.transact(USDC, cDAI).return_value == ZERO_ADDRESS


def test_multiple_pools(registry_all, DAI, USDC, pool_compound, pool_y, pool_susd):
    pools = set([pool_susd.address, pool_compound.address, pool_y.address])
    for i in range(3):
        pools.discard(str(registry_all.find_pool_for_coins.transact(DAI, USDC, i).return_value))

    assert not pools


def test_no_registry(registry, DAI, USDC):
    assert registry.find_pool_for_coins.transact(DAI, USDC).return_value == ZERO_ADDRESS
