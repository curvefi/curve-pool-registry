import pytest
from brownie import ERC20, ERC20NoReturn, ERC20ReturnFalse, cERC20, compile_source, yERC20

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ADDR_PROVIDER = "0x0000000022D53366457F9d5E68Ec105046FC4383"

RATE_METHOD_IDS = {
    "cERC20": cERC20.signatures["exchangeRateStored"],
    "yERC20": yERC20.signatures["getPricePerFullShare"],
}


# setup


def pytest_addoption(parser):
    parser.addoption(
        "--once", action="store_true", help="Only run each test once (no parametrization)"
    )


def pytest_configure(config):
    # add custom markers
    config.addinivalue_line("markers", "once: only run this test once (no parametrization)")
    config.addinivalue_line("markers", "params: test parametrization filters")
    config.addinivalue_line(
        "markers",
        "itercoins: parametrize a test with one or more ranges, "
        "equal to `n_coins` for the active pool",
    )
    config.addinivalue_line(
        "markers",
        "itermetacoins: parametrize a test with one or more ranges, "
        "equal to `n_metacoins` for the active pool",
    )


def pytest_generate_tests(metafunc):
    # apply initial parametrization of `itercoins`
    for marker in metafunc.definition.iter_markers(name="itercoins"):
        for item in marker.args:
            metafunc.parametrize(item, range(9))

    # apply initial parametrization of `itermetacoins`
    for marker in metafunc.definition.iter_markers(name="itermetacoins"):
        for item in marker.args:
            metafunc.parametrize(item, range(9))


def pytest_collection_modifyitems(config, items):
    seen = {}
    for item in items.copy():
        # remove excess `itercoins` parametrized tests
        marker = next(item.iter_markers(name="itercoins"), False)
        if marker:
            n_coins = item.callspec.params["n_coins"]

            limit = marker.kwargs.get("max", 9)
            values = [item.callspec.params[i] for i in marker.args]
            if max(values) >= n_coins or len(set(values)) < len(values) or max(values) > limit:
                items.remove(item)
                continue

        # remove excess `itermetacoins` parametrized tests
        marker = next(item.iter_markers(name="itermetacoins"), False)
        if marker:
            n_coins = item.callspec.params["n_metacoins"]

            limit = marker.kwargs.get("max", 9)
            values = [item.callspec.params[i] for i in marker.args]
            if max(values) >= n_coins or len(set(values)) < len(values) or max(values) > limit:
                items.remove(item)
                continue

        # remove parametrized tests that do not match `params` marker kwargs
        marker = next(item.iter_markers(name="params"), False)
        if marker:
            params = item.callspec.params
            if next((k for k, v in marker.kwargs.items() if params.get(k) != v), None):
                items.remove(item)
                continue

        # filter parametrized tests when `once` is active
        # this must be the last filter applied, or we might completely skip a test
        if config.getoption("once") or next(item.iter_markers("once"), None):
            path = item.fspath
            seen.setdefault(path, set())
            if item.obj in seen[path]:
                items.remove(item)
                continue
            seen[path].add(item.obj)

    # hacky magic to ensure the correct number of tests is shown in collection report
    config.pluginmanager.get_plugin("terminalreporter")._numcollected = len(items)


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# simple deployment fixtures (no parametrization)


@pytest.fixture(scope="module")
def gauge_controller(GaugeControllerMock, alice):
    yield GaugeControllerMock.deploy({"from": alice})


@pytest.fixture(scope="module")
def calculator(CurveCalc, alice):
    yield CurveCalc.deploy({"from": alice})


@pytest.fixture(scope="module")
def provider(AddressProvider, alice):
    yield AddressProvider.deploy(alice, {"from": alice})


@pytest.fixture(scope="module")
def registry(Registry, alice, provider, gauge_controller):
    contract = Registry.deploy(provider, gauge_controller, {"from": alice})
    provider.set_address(0, contract, {"from": alice})
    yield contract


@pytest.fixture(scope="module")
def registry_pool_info(PoolInfo, alice, provider):
    yield PoolInfo.deploy(provider, {"from": alice})


@pytest.fixture(scope="module")
def registry_swap(Swaps, alice, provider, registry, calculator):
    provider.set_address(0, registry, {"from": alice})
    yield Swaps.deploy(provider, calculator, {"from": alice})


@pytest.fixture(scope="module")
def lp_token(alice):
    return ERC20.deploy("MetaTest Token", "MTST", 18, {"from": alice})


@pytest.fixture(scope="module")
def meta_lp_token(alice):
    return ERC20.deploy("MetaTest Token", "MTST", 18, {"from": alice})


# private deployments fixtures
# deploying prior to parametrization of the public fixtures avoids excessive deployments


@pytest.fixture(scope="module")
def _underlying_decimals():
    return [18, 8, 6, 18]


@pytest.fixture(scope="module")
def _wrapped_decimals():
    return [8, 12, 16, 18]


@pytest.fixture(scope="module")
def _meta_decimals():
    return [6, 18, 8]


@pytest.fixture(scope="module")
def _underlying_coins(_underlying_decimals, alice):
    deployers = [ERC20, ERC20NoReturn, ERC20ReturnFalse]
    coins = []
    for i, (deployer, decimals) in enumerate(zip(deployers, _underlying_decimals)):
        contract = deployer.deploy(f"Test Token {i}", f"TST{i}", decimals, {"from": alice})
        coins.append(contract)
    coins.append("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE")

    return coins


@pytest.fixture(scope="module")
def _wrapped_coins(_underlying_coins, _wrapped_decimals, lending, alice):
    coins = []
    for i, (coin, decimals) in enumerate(zip(_underlying_coins, _wrapped_decimals)):
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            coins.append(coin)
            continue
        contract = lending.deploy(
            f"Wrapped Test Token {i}", f"wTST{i}", decimals, coin, 10 ** 18, {"from": alice}
        )
        coins.append(contract)

    return coins


@pytest.fixture(scope="module")
def _meta_coins(_meta_decimals, alice):
    deployers = [ERC20, ERC20NoReturn, ERC20ReturnFalse]
    coins = []
    for i, (deployer, decimals) in enumerate(zip(deployers, _meta_decimals)):
        contract = deployer.deploy(f"MetaTest Token {i}", f"MT{i}", decimals, {"from": alice})
        coins.append(contract)

    return coins


# parametrized fixtures


@pytest.fixture(scope="module", params=(True, False), ids=("v1", "v2"))
def is_v1(request):
    return request.param


@pytest.fixture(scope="module", params=("yERC20", "cERC20"), ids=("yearn", "comp"))
def lending(request):
    yield globals()[request.param]


@pytest.fixture(scope="module", params=range(4, 1, -1), ids=(f"{i} coins" for i in range(4, 1, -1)))
def n_coins(_underlying_coins, request):
    return request.param


@pytest.fixture(
    scope="module", params=range(4, 1, -1), ids=(f"{i} metacoins" for i in range(4, 1, -1))
)
def n_metacoins(_meta_coins, request):
    return request.param


@pytest.fixture(scope="module")
def underlying_decimals(_underlying_decimals, n_coins):
    return _underlying_decimals[:n_coins]


@pytest.fixture(scope="module")
def wrapped_decimals(_wrapped_decimals, n_coins):
    return _wrapped_decimals[:n_coins]


@pytest.fixture(scope="module")
def meta_decimals(_meta_decimals, n_metacoins):
    return _meta_decimals[: n_metacoins - 1] + [18]


@pytest.fixture(scope="module")
def underlying_coins(alice, _underlying_coins, n_coins):
    return _underlying_coins[:n_coins]


@pytest.fixture(scope="module")
def wrapped_coins(_wrapped_coins, n_coins):
    return _wrapped_coins[:n_coins]


@pytest.fixture(scope="module")
def meta_coins(alice, _meta_coins, n_metacoins, lp_token):
    return _meta_coins[: n_metacoins - 1] + [lp_token]


@pytest.fixture(scope="module")
def rate_method_id(wrapped_coins):
    key = wrapped_coins[0]._name
    return RATE_METHOD_IDS[key]


@pytest.fixture(scope="module")
def swap(PoolMockV1, PoolMockV2, alice, underlying_coins, is_v1):

    if is_v1:
        deployer = PoolMockV1
    else:
        deployer = PoolMockV2

    n_coins = len(underlying_coins)
    underlying_coins = underlying_coins + [ZERO_ADDRESS] * (4 - len(underlying_coins))

    contract = deployer.deploy(
        n_coins, underlying_coins, [ZERO_ADDRESS] * 4, 70, 4000000, {"from": alice}
    )
    return contract


@pytest.fixture(scope="module")
def lending_swap(PoolMockV1, PoolMockV2, alice, wrapped_coins, underlying_coins, is_v1):
    if is_v1:
        deployer = PoolMockV1
    else:
        deployer = PoolMockV2

    n_coins = len(underlying_coins)
    wrapped_coins = wrapped_coins + [ZERO_ADDRESS] * (4 - len(wrapped_coins))
    underlying_coins = underlying_coins + [ZERO_ADDRESS] * (4 - len(underlying_coins))

    contract = deployer.deploy(
        n_coins, wrapped_coins, underlying_coins, 70, 4000000, {"from": alice}
    )
    return contract


@pytest.fixture(scope="module")
def meta_swap(MetaPoolMock, alice, swap, meta_coins, underlying_coins, n_metacoins, n_coins):
    meta_coins = meta_coins + [ZERO_ADDRESS] * (4 - len(meta_coins))
    underlying_coins = underlying_coins + [ZERO_ADDRESS] * (4 - len(underlying_coins))
    return MetaPoolMock.deploy(
        n_metacoins, n_coins, swap, meta_coins, underlying_coins, 70, 4000000, {"from": alice}
    )


@pytest.fixture(scope="module")
def liquidity_gauge(LiquidityGaugeMock, alice, gauge_controller, lp_token):
    gauge = LiquidityGaugeMock.deploy(lp_token, {"from": alice})
    gauge_controller._set_gauge_type(gauge, 1, {"from": alice})
    yield gauge


@pytest.fixture(scope="module")
def liquidity_gauge_meta(LiquidityGaugeMock, alice, gauge_controller, meta_lp_token):
    gauge = LiquidityGaugeMock.deploy(meta_lp_token, {"from": alice})
    gauge_controller._set_gauge_type(gauge, 2, {"from": alice})
    yield gauge


@pytest.fixture(scope="module")
def gauge_implementation(alice, MockGauge, provider):
    NewMockGauge = compile_source(
        MockGauge._build["source"].replace(ADDR_PROVIDER, provider.address), vyper_version="0.2.15"
    ).Vyper
    return NewMockGauge.deploy({"from": alice})


@pytest.fixture(scope="module")
def mock_factory(alice, MockFactory, gauge_implementation, provider):
    factory = MockFactory.deploy(gauge_implementation, {"from": alice})
    # give the factory id # 3
    while provider.max_id() < 4:
        provider.add_new_id(factory, "Metapool Factory", {"from": alice})
    return factory


@pytest.fixture(scope="module")
def gauge_registry(alice, provider, GaugeRegistry, mock_factory):
    NewGaugeRegistry = compile_source(
        GaugeRegistry._build["source"].replace(ADDR_PROVIDER, provider.address),
        vyper_version="0.2.15",
    ).Vyper
    gauge_registry = NewGaugeRegistry.deploy({"from": alice})
    # add to address provider at id = 5
    while provider.max_id() < 6:
        provider.add_new_id(gauge_registry, "Gauge Registry", {"from": alice})
    return gauge_registry
