import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_get_rates_compound(accounts, registry_compound, pool_compound, cDAI):
    assert registry_compound.get_pool_rates.call(pool_compound) == [10**18, 10**18, 0, 0, 0, 0, 0, 0]

    cDAI._set_exchange_rate(31337, {'from': accounts[0]})
    assert registry_compound.get_pool_rates.call(pool_compound) == [31337, 10**18, 0, 0, 0, 0, 0, 0]


def test_get_rates_y(accounts, registry_y, pool_y, yDAI):
    assert registry_y.get_pool_rates.call(pool_y) == [10**18, 10**18, 10**18, 10**18, 0, 0, 0, 0]

    yDAI._set_exchange_rate(31337, {'from': accounts[0]})
    assert registry_y.get_pool_rates.call(pool_y) == [31337, 10**18, 10**18, 10**18, 0, 0, 0, 0]


def test_pool_without_lending(accounts, registry_susd, pool_susd):
    assert registry_susd.get_pool_rates.call(pool_susd) == [10**18, 10**18, 10**18, 10**18, 0, 0, 0, 0]


def test_unknown_pool(accounts, registry):
    assert registry.get_pool_rates.call(accounts[-1]) == [0, 0, 0, 0, 0, 0, 0, 0]


def test_removed_pool(accounts, registry_y, pool_y, yDAI):
    yDAI._set_exchange_rate(31337, {'from': accounts[0]})
    assert registry_y.get_pool_rates.call(pool_y) == [31337, 10**18, 10**18, 10**18, 0, 0, 0, 0]

    registry_y.remove_pool(pool_y)
    assert registry_y.get_pool_rates.call(pool_y) == [0, 0, 0, 0, 0, 0, 0, 0]


def test_fix_incorrect_calldata(accounts, registry, pool_compound, lp_compound, cDAI):
    registry.add_pool(
        pool_compound,
        2,
        lp_compound,
        "0xdEAdbEEf",
        [8, 8, 0, 0, 0, 0, 0, 0],
        [18, 6, 0, 0, 0, 0, 0, 0],
        {'from': accounts[0]}
    )

    with brownie.reverts("dev: bad response"):
        registry.get_pool_rates.call(pool_compound)

    registry.remove_pool(pool_compound)
    registry.add_pool(
        pool_compound,
        2,
        lp_compound,
        cDAI.exchangeRateStored.signature,
        [8, 8, 0, 0, 0, 0, 0, 0],
        [18, 6, 0, 0, 0, 0, 0, 0],
        {'from': accounts[0]}
    )

    assert registry.get_pool_rates.call(pool_compound) == [10**18, 10**18, 0, 0, 0, 0, 0, 0]


def test_without_underlying(accounts, registry, pool_compound, cDAI, cUSDC):
    registry.add_pool_without_underlying(
        pool_compound,
        2,
        ZERO_ADDRESS,
        cDAI.exchangeRateStored.signature,
        [8, 8, 0, 0, 0, 0, 0, 0],
        [True] + [False] * 7,
        {'from': accounts[0]}
    )

    assert registry.get_pool_rates.call(pool_compound) == [10**18, 10**18, 0, 0, 0, 0, 0, 0]

    cDAI._set_exchange_rate(31337, {'from': accounts[0]})
    cUSDC._set_exchange_rate(31337, {'from': accounts[0]})

    assert registry.get_pool_rates.call(pool_compound) == [31337, 10**18, 0, 0, 0, 0, 0, 0]
