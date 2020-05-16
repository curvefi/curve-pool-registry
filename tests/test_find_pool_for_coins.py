import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture
def registry_all(accounts, registry, pool_compound, pool_y, pool_susd):
    registry.add_pool(pool_compound, 2, [18, 6, 0, 0, 0, 0, 0], b"", {'from': accounts[0]})

    for pool in (pool_y, pool_susd):
        registry.add_pool(pool, 4, [18, 6, 6, 18, 0, 0, 0], b"", {'from': accounts[0]})

    yield registry


@pytest.fixture
def registry_compound(accounts, registry, pool_compound):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"\x4d\x89\x6d\xbd",
        {'from': accounts[0]}
    )

    yield registry

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
