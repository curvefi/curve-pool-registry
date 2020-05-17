import brownie
import pytest


def test_amount_dy(accounts, registry, pool_compound, cDAI, cUSDC):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        cDAI.exchangeRateStored.signature,
        {'from': accounts[0]}
    )

    # 0 and 1 correspond to cDAI and cUSDC in the pool
    dy = pool_compound.get_dy(0, 1, 10**18)
    assert registry.get_exchange_amount(pool_compound, cDAI, cUSDC, 10**18) == dy

    dy = pool_compound.get_dy(1, 0, 10**18)
    assert registry.get_exchange_amount(pool_compound, cUSDC, cDAI, 10**18) == dy


def test_amount_dy_underlying(accounts, registry, pool_compound, DAI, USDC):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    # 0 and 1 correspond to DAI and USDC in the pool
    dy = pool_compound.get_dy_underlying(0, 1, 10**18)
    assert registry.get_exchange_amount(pool_compound, DAI, USDC, 10**18) == dy

    dy = pool_compound.get_dy_underlying(1, 0, 10**18)
    assert registry.get_exchange_amount(pool_compound, USDC, DAI, 10**18) == dy


def test_amount_no_market(accounts, registry, pool_compound, DAI, USDT):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )
    with brownie.reverts("No available market"):
        registry.get_exchange_amount(pool_compound, DAI, USDT, 10**18)


def test_unknown_pool(registry, pool_compound, DAI, USDC):
    with brownie.reverts("No available market"):
        registry.get_exchange_amount(pool_compound, DAI, USDC, 10**18)


def test_no_market_no_lending(accounts, registry, pool_susd, DAI, cUSDC):
    registry.add_pool(
        pool_susd,
        4,
        [18, 6, 6, 18, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    with brownie.reverts("No available market"):
        registry.get_exchange_amount(pool_susd, DAI, cUSDC, 10**18)


def test_same_token(accounts, registry, pool_compound, DAI):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    with brownie.reverts("No available market"):
        registry.get_exchange_amount(pool_compound, DAI, DAI, 10**18)


def test_same_token_underlying(accounts, registry, pool_compound, cDAI):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    with brownie.reverts("No available market"):
        registry.get_exchange_amount(pool_compound, cDAI, cDAI, 10**18)
