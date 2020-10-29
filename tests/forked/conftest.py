import brownie
import requests
import pytest
from brownie import Contract
from brownie.convert import to_address

from scripts.add_pools import add_pool
from scripts.get_pool_data import get_pool_data

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
_holders = {}
_pooldata = get_pool_data()


def pytest_addoption(parser):
    parser.addoption("--pool", help="comma-separated list of pools to target")
    parser.addoption("--once", action="store_true", help="Only run each test once per pool")


def pytest_configure(config):
    # add custom markers
    config.addinivalue_line("markers", "once: only run this test once (no parametrization)")
    config.addinivalue_line("markers", "params: test parametrization filters")
    config.addinivalue_line("markers", "meta: only run test against metapools")
    config.addinivalue_line("markers", "skip_meta: do not run test against metapools")
    config.addinivalue_line(
        "markers",
        "itercoins: parametrize a test with one or more ranges, "
        "equal to `n_coins` for the active pool"
    )


def pytest_generate_tests(metafunc):
    # apply initial parametrization of `itercoins`
    for marker in metafunc.definition.iter_markers(name="itercoins"):
        for item in marker.args:
            metafunc.parametrize(item, range(9))


def pytest_collection_modifyitems(config, items):

    target_pool = config.getoption("pool")
    if target_pool:
        target_pool = target_pool.split(",")
    seen = {}

    for item in items.copy():
        pool_name = item.callspec.params['pool_data']
        pool_data = _pooldata[pool_name]
        base_pool = pool_data.get('base_pool')
        if target_pool and pool_name not in target_pool:
            items.remove(item)
            continue

        if base_pool:
            if next(item.iter_markers(name="skip_meta"), None):
                items.remove(item)
                continue
        else:
            if next(item.iter_markers(name="meta"), None):
                items.remove(item)
                continue

        # remove excess `itercoins` parametrized tests
        marker = next(item.iter_markers(name="itercoins"), False)
        if marker:
            is_underlying = marker.kwargs.get("underlying")
            if is_underlying and base_pool:
                # for metacoins, underlying must include the base pool
                n_coins = len(pool_data['coins']) + len(_pooldata[base_pool]["coins"])
            else:
                n_coins = len(pool_data['coins'])

            # apply `max` kwarg
            limit = min(n_coins-1, marker.kwargs.get("max", n_coins))

            values = [item.callspec.params[i] for i in marker.args]
            if len(set(values)) < len(values) or max(values) > limit:
                items.remove(item)
                continue

            if not is_underlying:
                # skip if `itercoins` is not marked as underlying and pool has no wrapped coins
                if next(
                    (True for i in values if "wrapped_decimals" not in pool_data["coins"][i]),
                    False,
                ):
                    items.remove(item)
                    continue

        # filter parametrized tests when `once` is active
        # this must be the last filter applied, or we might completely skip a test
        if config.getoption("once") or next(item.iter_markers("once"), None):
            path = item.fspath
            seen.setdefault(pool_name, {}).setdefault(path, set())

            if item.obj in seen[pool_name][path]:
                items.remove(item)
                continue
            seen[pool_name][path].add(item.obj)

    # hacky magic to ensure the correct number of tests is shown in collection report
    config.pluginmanager.get_plugin("terminalreporter")._numcollected = len(items)


def pytest_collection_finish(session):
    # default to forked mainnet
    if session.items:
        brownie.network.connect('mainnet-fork')


@pytest.fixture(scope="session", params=_pooldata.keys())
def pool_data(request):
    # main parametrization fixture, pulls pool data from `./pooldata.json`
    return _pooldata[request.param]


@pytest.fixture(scope="session")
def base_pool_data(pool_data):
    if "base_pool" in pool_data:
        return _pooldata[pool_data["base_pool"]]
    else:
        return None


@pytest.fixture(scope="module")
def provider(AddressProvider, alice):
    yield AddressProvider.deploy(alice, {'from': alice})


@pytest.fixture(scope="module")
def registry(Registry, pool_data, base_pool_data, alice, provider, gauge_controller):
    registry = Registry.deploy(provider, gauge_controller, {'from': alice})
    if base_pool_data:
        add_pool(base_pool_data, registry, alice)

    add_pool(pool_data, registry, alice)

    yield registry


@pytest.fixture(scope="module")
def registry_swap(RegistrySwap, alice, registry, calculator):
    yield RegistrySwap.deploy(registry, calculator, {'from': alice})


@pytest.fixture(scope="module")
def calculator(CurveCalc, alice):
    yield CurveCalc.deploy({'from': alice})


@pytest.fixture(scope="module")
def swap(pool_data):
    yield Contract(pool_data['swap_address'])


@pytest.fixture(scope="module")
def base_swap(base_pool_data):
    if base_pool_data:
        return Contract(base_pool_data['swap_address'])
    else:
        return None


@pytest.fixture(scope="module")
def lp_token(pool_data):
    yield Contract(pool_data['lp_token_address'])


@pytest.fixture(scope="module")
def n_coins(pool_data):
    yield len(pool_data['coins'])


@pytest.fixture(scope="module")
def gauge_controller():
    yield Contract("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")


class _MintableTestToken(Contract):

    _rate_methods = (
        "exchangeRateStored",
        "exchangeRateCurrent",
        "getPricePerFullShare",
        "get_virtual_price",
    )

    def __init__(self, coin_data, is_wrapped):
        self._coin_data = coin_data

        wrapped_address = coin_data.get("wrapped_address")
        underlying_address = coin_data.get("underlying_address")
        if is_wrapped:
            address = wrapped_address or underlying_address
        else:
            address = underlying_address or wrapped_address
        super().__init__(address)

        if is_wrapped and wrapped_address:
            self._rate_fn = next(getattr(self, i) for i in self._rate_methods if hasattr(self, i))
        else:
            if "base_pool_token" in coin_data:
                base_pool = next(i for i in _pooldata.values() if i.get("lp_token_address") == self.address)
                self._rate_fn = Contract(base_pool["swap_address"]).get_virtual_price
            else:
                self._rate_fn = None

        # get top token holder addresses
        address = self.address
        if address not in _holders:
            holders = requests.get(
                f"https://api.ethplorer.io/getTopTokenHolders/{address}",
                params={'apiKey': "freekey", 'limit': 50},
            ).json()
            _holders[address] = [to_address(i['address']) for i in holders['holders']]

    def _get_rate(self):
        if not self._rate_fn:
            return 10**18
        return self._rate_fn.call()

    def _mint_for_testing(self, target, amount, tx=None):
        if self.address == "0x674C6Ad92Fd080e4004b2312b45f796a192D27a0":
            # USDN
            self.deposit(target, amount, {'from': "0x90f85042533F11b362769ea9beE20334584Dcd7D"})
            return
        if self.address == "0x0E2EC54fC0B509F445631Bf4b91AB8168230C752":
            # LinkUSD
            self.mint(target, amount, {'from': "0x62F31E08e279f3091d9755a09914DF97554eAe0b"})
            return
        if self.address == "0x196f4727526eA7FB1e17b2071B3d8eAA38486988":
            self.changeMaxSupply(2**128, {'from': self.owner()})
            self.mint(target, amount, {'from': self.minter()})
            return

        for address in _holders[self.address].copy():
            if address == self.address:
                # don't claim from the treasury - that could cause wierdness
                continue

            balance = self.balanceOf(address)
            if amount > balance:
                self.transfer(target, balance, {'from': address})
                amount -= balance
            else:
                self.transfer(target, amount, {'from': address})
                return

        raise ValueError(f"Insufficient tokens available to mint {self.name()}")


@pytest.fixture(scope="module")
def wrapped_coins(pool_data):
    yield [_MintableTestToken(i, True) for i in pool_data['coins']]


@pytest.fixture(scope="module")
def underlying_coins(pool_data, base_pool_data):
    if base_pool_data:
        coins = [_MintableTestToken(i, False) for i in pool_data['coins'][:-1]]
        coins += [_MintableTestToken(i, False) for i in base_pool_data["coins"]]
        yield coins
    else:
        yield [_MintableTestToken(i, False) for i in pool_data['coins']]


@pytest.fixture(scope="module")
def underlying_decimals(pool_data, base_pool_data):
    # number of decimal places for each underlying coin in the active pool
    decimals = [i.get('decimals', i.get('wrapped_decimals')) for i in pool_data['coins']]

    if base_pool_data is None:
        return decimals
    base_decimals = [i.get('decimals', i.get('wrapped_decimals')) for i in base_pool_data['coins']]
    return decimals[:-1] + base_decimals


@pytest.fixture(scope="module")
def wrapped_decimals(pool_data):
    # number of decimal places for each wrapped coin in the active pool
    yield [i.get('wrapped_decimals', i.get('decimals')) for i in pool_data['coins']]
