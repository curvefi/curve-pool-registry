import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# setup

@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# registry

@pytest.fixture(scope="module")
def registry(Registry, accounts):
    yield Registry.deploy({'from': accounts[0]})


# curve pools

@pytest.fixture(scope="module")
def pool_compound(PoolMock, accounts, DAI, USDC, cDAI, cUSDC):
    coins = [cDAI, cUSDC, ZERO_ADDRESS, ZERO_ADDRESS]
    underlying = [DAI, USDC, ZERO_ADDRESS, ZERO_ADDRESS]
    yield PoolMock.deploy(2, coins, underlying, 70, 4000000, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_y(PoolMock, accounts, DAI, USDC, USDT, TUSD, yDAI, yUSDC, yUSDT, yTUSD):
    coins = [yDAI, yUSDC, yUSDT, yTUSD]
    underlying = [DAI, USDC, USDT, TUSD]
    yield PoolMock.deploy(4, coins, underlying, 70, 4000000, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool_susd(PoolMock, accounts, DAI, USDC, USDT, sUSD):
    coins = [DAI, USDC, USDT, sUSD]
    yield PoolMock.deploy(4, coins, coins, 70, 4000000, {'from': accounts[0]})


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
