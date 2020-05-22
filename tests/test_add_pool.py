import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_add_to_pool_list(registry_compound, pool_compound):
    assert registry_compound.pool_count() == 1
    assert registry_compound.pool_list(0) == pool_compound


def test_approval(registry_compound, pool_compound, DAI, cDAI):
    assert DAI.allowance(registry_compound, pool_compound) == 2**256 - 1
    assert cDAI.allowance(registry_compound, pool_compound) == 2**256 - 1


def test_get_pool_coins(registry_compound, pool_compound):
    coin_info = registry_compound.get_pool_coins(pool_compound)

    assert coin_info['coins'] == [pool_compound.coins(0),  pool_compound.coins(1)] + [ZERO_ADDRESS] * 5
    assert coin_info['decimals'] == [18, 6, 0, 0, 0, 0, 0]

    expected = [pool_compound.underlying_coins(0), pool_compound.underlying_coins(1)] + [ZERO_ADDRESS] * 5
    assert coin_info['underlying_coins'] == expected


def test_admin_only(accounts, registry, pool_compound, lp_compound):
    with brownie.reverts("dev: admin-only function"):
        registry.add_pool(
            pool_compound,
            2,
            lp_compound,
            [18, 6, 0, 0, 0, 0, 0],
            b"\x4d\x89\x6d\xbd",
            {'from': accounts[1]}
        )


def test_cannot_add_twice(accounts, registry_compound, pool_compound, lp_compound):
    with brownie.reverts("dev: pool exists"):
        registry_compound.add_pool(
            pool_compound,
            2,
            lp_compound,
            [18, 6, 0, 0, 0, 0, 0],
            b"\x4d\x89\x6d\xbd",
            {'from': accounts[0]}
        )


def test_add_multiple(accounts, registry, pool_y, pool_susd, lp_y):
    for pool in (pool_y, pool_susd):
        registry.add_pool(
            pool,
            4,
            lp_y,
            [18, 6, 6, 18, 0, 0, 0],
            b"\x4d\x89\x6d\xbd",
            {'from': accounts[0]}
        )

    assert registry.pool_count() == 2
    assert registry.pool_list(0) == pool_y
    assert registry.pool_list(1) == pool_susd

    for pool in [pool_y, pool_susd]:
        coin_info = registry.get_pool_coins(pool)
        assert coin_info['decimals'] == [18, 6, 6, 18, 0, 0, 0]
        for i in range(4):
            assert coin_info['coins'][i] == pool.coins(i)
            assert coin_info['underlying_coins'][i] == pool.underlying_coins(i)


def test_get_pool_info(accounts, registry, pool_y, pool_susd, lp_y, lp_susd):
    registry.add_pool(pool_y, 4, lp_y, [1, 2, 3, 4, 0, 0, 0], b"", {'from': accounts[0]})
    y_pool_info = registry.get_pool_info(pool_y)

    registry.add_pool(pool_susd, 4, lp_susd, [33, 44, 55, 66, 0, 0, 0], b"", {'from': accounts[0]})
    susd_pool_info = registry.get_pool_info(pool_susd)

    assert y_pool_info != susd_pool_info
