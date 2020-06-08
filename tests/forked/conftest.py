import pytest

from scripts.utils import pack_values, right_pad

@pytest.fixture(scope="module")
def pool_renbtc(Contract):
    yield Contract("0x93054188d876f558f4a66B2EF1d97d16eDf0895B")


@pytest.fixture(scope="module")
def lp_renbtc(Contract):
    yield Contract("0x49849C98ae39Fff122806C06791Fa73784FB3675")


@pytest.fixture(scope="module")
def RenBTC(Contract):
    yield Contract("0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D")


@pytest.fixture(scope="module")
def WBTC(Contract):
    yield Contract("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")


@pytest.fixture(scope="module")
def registry_renbtc(accounts, registry, calculator, pool_renbtc, lp_renbtc):
    registry.add_pool_without_underlying(
        pool_renbtc,
        2,
        lp_renbtc,
        calculator,
        right_pad("0xbd6d894d"),
        pack_values([8, 8]),
        pack_values([True] + [False] * 7),
        {'from': accounts[0]}
    )

    yield registry
