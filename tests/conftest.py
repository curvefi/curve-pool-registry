import pytest

from scripts.utils import pack_values, right_pad

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


# setup

@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# registries

@pytest.fixture(scope="module")
def registry(Registry, accounts, gauge_controller):
    yield Registry.deploy(gauge_controller, {'from': accounts[0]})


@pytest.fixture(scope="module")
def registry_compound(accounts, Registry, gauge_controller, pool_compound, calculator, lp_compound, gauge_compound, cDAI, USDT):
    registry = Registry.deploy(gauge_controller, {'from': accounts[0]})
    registry.add_pool(
        pool_compound,
        2,
        lp_compound,
        gauge_compound,
        calculator,
        right_pad(cDAI.exchangeRateStored.signature),
        pack_values([8, 8]),
        pack_values([18, 6]),
        True,
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_y(Registry, accounts, gauge_controller, pool_y, calculator, lp_y, gauge_y, yDAI, USDT):
    registry = Registry.deploy(gauge_controller, {'from': accounts[0]})
    registry.add_pool(
        pool_y,
        4,
        lp_y,
        gauge_y,
        calculator,
        right_pad(yDAI.getPricePerFullShare.signature),
        pack_values([18, 6, 6, 18]),
        pack_values([18, 6, 6, 18]),
        True,
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_susd(Registry, accounts, gauge_controller, pool_susd, calculator, lp_susd, gauge_susd, USDT):
    registry = Registry.deploy(gauge_controller, {'from': accounts[0]})
    registry.add_pool(
        pool_susd,
        4,
        lp_susd,
        gauge_susd,
        calculator,
        "0x00",
        pack_values([18, 6, 6, 18]),
        pack_values([18, 6, 6, 18]),
        True,
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_eth(Registry, accounts, gauge_controller, pool_eth, lp_y, gauge_y, USDT, yDAI):
    registry = Registry.deploy(gauge_controller, {'from': accounts[0]})
    registry.add_pool(
        pool_eth,
        3,
        lp_y,
        gauge_y,
        ZERO_ADDRESS,
        right_pad(yDAI.getPricePerFullShare.signature),
        "0x00",
        "0x00",
        True,
        {'from': accounts[0]}
    )

    yield registry


@pytest.fixture(scope="module")
def registry_all(
    Registry, accounts, gauge_controller,
    pool_compound, pool_y, pool_susd,
    gauge_compound, gauge_y, gauge_susd,
    cDAI, yDAI, USDT,
    calculator, lp_compound, lp_y, lp_susd
):
    registry = Registry.deploy(gauge_controller, {'from': accounts[0]})

    registry.add_pool(
        pool_compound,
        2,
        lp_compound,
        gauge_compound,
        calculator,
        right_pad(cDAI.exchangeRateStored.signature),
        pack_values([8, 8]),
        pack_values([18, 6]),
        True,
        {'from': accounts[0]}
    )
    registry.add_pool(
        pool_y,
        4,
        lp_y,
        gauge_y,
        calculator,
        right_pad(yDAI.getPricePerFullShare.signature),
        pack_values([18, 6, 6, 18]),
        pack_values([18, 6, 6, 18]),
        True,
        {'from': accounts[0]}
    )
    registry.add_pool(
        pool_susd,
        4,
        lp_susd,
        gauge_susd,
        calculator,
        "0x00",
        pack_values([18, 6, 6, 18]),
        pack_values([18, 6, 6, 18]),
        True,
        {'from': accounts[0]}
    )

    yield registry


# calculator

@pytest.fixture(scope="module")
def calculator(CurveCalc, accounts):
    yield CurveCalc.deploy({'from': accounts[0]})


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


@pytest.fixture(scope="module")
def pool_eth(PoolMock, accounts, DAI, USDT, yDAI, yUSDT):
    coins = [yDAI, yUSDT, "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", ZERO_ADDRESS]
    underlying = [DAI, USDT, "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", ZERO_ADDRESS]
    pool = PoolMock.deploy(3, coins, underlying, 70, 4000000, {'from': accounts[0]})
    accounts[-1].transfer(pool, accounts[-1].balance())
    yield pool


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


# liquidity gauges

@pytest.fixture(scope="module")
def gauge_controller(GaugeControllerMock, accounts):
    yield GaugeControllerMock.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def gauge_compound(LiquidityGaugeMock, accounts, gauge_controller, lp_compound):
    gauge = LiquidityGaugeMock.deploy(lp_compound, {'from': accounts[0]})
    gauge_controller._set_gauge_type(gauge, 1, {'from': accounts[0]})
    yield gauge


@pytest.fixture(scope="module")
def gauge_y(LiquidityGaugeMock, accounts, gauge_controller, lp_y):
    gauge = LiquidityGaugeMock.deploy(lp_y, {'from': accounts[0]})
    gauge_controller._set_gauge_type(gauge, 2, {'from': accounts[0]})
    yield gauge


@pytest.fixture(scope="module")
def gauge_susd(LiquidityGaugeMock, accounts, gauge_controller, lp_susd):
    gauge = LiquidityGaugeMock.deploy(lp_susd, {'from': accounts[0]})
    gauge_controller._set_gauge_type(gauge, 3, {'from': accounts[0]})
    yield gauge


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
