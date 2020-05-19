import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_find_coin_pool(registry_compound, cDAI, cUSDC, pool_compound):
    assert registry_compound.find_pool_for_coins(cDAI, cUSDC) == pool_compound
    assert registry_compound.find_pool_for_coins(cUSDC, cDAI) == pool_compound


def test_find_underlying_coin_pool(registry_compound, DAI, USDC, pool_compound):
    assert registry_compound.find_pool_for_coins(DAI, USDC) == pool_compound
    assert registry_compound.find_pool_for_coins(USDC, DAI) == pool_compound


def test_no_pool_coin_underlying_mismatch(registry_compound, cDAI, USDC, pool_compound):
    assert registry_compound.find_pool_for_coins(cDAI, USDC) == ZERO_ADDRESS
    assert registry_compound.find_pool_for_coins(USDC, cDAI) == ZERO_ADDRESS


def test_multiple_pools(registry_all, DAI, USDC, pool_compound, pool_y, pool_susd):
    pools = set([pool_susd.address, pool_compound.address, pool_y.address])
    for i in range(3):
        pools.discard(str(registry_all.find_pool_for_coins(DAI, USDC, i)))

    assert not pools


def test_no_registry(registry, DAI, USDC):
    assert registry.find_pool_for_coins(DAI, USDC) == ZERO_ADDRESS
