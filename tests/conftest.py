import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# setup

@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# registries

@pytest.fixture(scope="module")
def registry(Registry, accounts, USDT):
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    yield Registry.deploy(returns_none, {'from': accounts[0]})


@pytest.fixture(scope="module")
def registry_compound(accounts, Registry, pool_compound, lp_compound, cDAI, USDT):
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    registry = Registry.deploy(returns_none, {'from': accounts[0]})
    registry.add_pool(
        pool_compound,
        2,
        lp_compound,
        [18, 6, 0, 0, 0, 0, 0, 0],
        cDAI.exchangeRateStored.signature,
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_y(Registry, accounts, pool_y, lp_y, yDAI, USDT):
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    registry = Registry.deploy(returns_none, {'from': accounts[0]})
    registry.add_pool(
        pool_y,
        4,
        lp_y,
        [18, 6, 6, 18, 0, 0, 0, 0],
        yDAI.getPricePerFullShare.signature,
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_susd(Registry, accounts, pool_susd, lp_susd, USDT):
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    registry = Registry.deploy(returns_none, {'from': accounts[0]})
    registry.add_pool(
        pool_susd,
        4,
        lp_susd,
        [18, 6, 6, 18, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_all(
    Registry, accounts,
    pool_compound, pool_y, pool_susd,
    cDAI, yDAI, USDT,
    lp_compound, lp_y, lp_susd
):
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    registry = Registry.deploy(returns_none, {'from': accounts[0]})

    registry.add_pool(
        pool_compound,
        2,
        lp_compound,
        [18, 6, 0, 0, 0, 0, 0, 0],
        cDAI.exchangeRateStored.signature,
        {'from': accounts[0]}
    )
    registry.add_pool(
        pool_y,
        4,
        lp_y,
        [18, 6, 6, 18, 0, 0, 0, 0],
        yDAI.getPricePerFullShare.signature,
        {'from': accounts[0]}
    )
    registry.add_pool(
        pool_susd,
        4,
        lp_susd,
        [18, 6, 6, 18, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    yield registry


# curve pools

@pytest.fixture(scope="module")
def pool_compound(PoolMock, accounts, DAI, USDC, cDAI, cUSDC):
    coins = [cDAI, cUSDC, ZERO_ADDRESS, ZERO_ADDRESS]
    underlying = [DAI, USDC, ZERO_ADDRESS, ZERO_ADDRESS]
    returns_none = [ZERO_ADDRESS] * 4
    yield PoolMock.deploy(2, coins, underlying, returns_none, 70, 4000000, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_y(PoolMock, accounts, DAI, USDC, USDT, TUSD, yDAI, yUSDC, yUSDT, yTUSD):
    coins = [yDAI, yUSDC, yUSDT, yTUSD]
    underlying = [DAI, USDC, USDT, TUSD]
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    yield PoolMock.deploy(4, coins, underlying, returns_none, 70, 4000000, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_susd(PoolMock, accounts, DAI, USDC, USDT, sUSD):
    coins = [DAI, USDC, USDT, sUSD]
    returns_none = [USDT, ZERO_ADDRESS, ZERO_ADDRESS, ZERO_ADDRESS]
    yield PoolMock.deploy(4, coins, coins, returns_none, 70, 4000000, {'from': accounts[0]})

# lp tokens

@pytest.fixture(scope="module")
def lp_compound(ERC20, accounts):
    yield ERC20.deploy("Curve Compound LP Token", "lpCOMP", 18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def lp_y(ERC20, accounts):
    yield ERC20.deploy("Curve Y LP Token", "lpY", 18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def lp_susd(ERC20, accounts):
    yield ERC20.deploy("Curve sUSD LP Token", "lpSUSD", 18, {"from": accounts[0]})


# base stablecoins

@pytest.fixture(scope="module")
def DAI(ERC20, accounts):
    yield ERC20.deploy("DAI", "DAI Stablecoin", 18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def USDC(ERC20, accounts):
    yield ERC20.deploy("USDC", "USD//C", 6, {"from": accounts[0]})


@pytest.fixture(scope="module")
def USDT(ERC20NoReturn, accounts):
    yield ERC20NoReturn.deploy("USDT", "Tether USD", 6, {"from": accounts[0]})


@pytest.fixture(scope="module")
def TUSD(ERC20, accounts):
    yield ERC20.deploy("TUSD", "TrueUSD", 18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def sUSD(ERC20, accounts):
    yield ERC20.deploy("sUSD", "Synth sUSD", 18, {"from": accounts[0]})


# compound wrapped stablecoins

@pytest.fixture(scope="module")
def cDAI(cERC20, accounts, DAI):
    yield cERC20.deploy("cDAI", "Compound Dai", 8, DAI, 10**18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def cUSDC(cERC20, accounts, USDC):
    yield cERC20.deploy("cUSDC", "Compound USD Coin", 8, USDC, 10**18, {"from": accounts[0]})


# iearn wrapped stablecoins

@pytest.fixture(scope="module")
def yDAI(yERC20, accounts, DAI):
    yield yERC20.deploy("yDAI", "iearn DAI", 18, DAI, 10**18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def yUSDC(yERC20, accounts, USDC):
    yield yERC20.deploy("yUSDC", "iearn USDC", 6, USDC, 10**18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def yUSDT(yERC20, accounts, USDT):
    yield yERC20.deploy("yUSDC", "iearn USDT", 6, USDT, 10**18, {"from": accounts[0]})


@pytest.fixture(scope="module")
def yTUSD(yERC20, accounts, TUSD):
    yield yERC20.deploy("yTUSDT", "iearn TUSD", 18, TUSD, 10**18, {"from": accounts[0]})


# token that returns false on a failed transfer

@pytest.fixture(scope="module")
def BAD(ERC20ReturnFalse, accounts):
    yield ERC20ReturnFalse.deploy("BAD", "Bad Token", 18, {'from': accounts[0]})
