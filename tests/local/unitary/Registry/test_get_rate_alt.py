import pytest
from brownie import ankrETH
from brownie.test import given, strategy

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def ankr_swap(PoolMockV2, alice):
    underlying_coins = ["0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"]
    wrapped_coins = [ankrETH.deploy({"from": alice})] + [ZERO_ADDRESS] * 3
    underlying_coins = underlying_coins + [ZERO_ADDRESS] * 3

    contract = PoolMockV2.deploy(1, wrapped_coins, underlying_coins, 70, 4000000, {"from": alice})
    return contract


@pytest.fixture(scope="module")
def registry(ERC20, Registry, RateCalcMock, provider, gauge_controller, alice, ankr_swap, lp_token):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    rate_calc = RateCalcMock.deploy({"from": alice})

    registry.add_pool(
        ankr_swap,
        1,
        lp_token,
        rate_calc.address + "71ca337d",
        pack_values([18]),
        pack_values([18]),
        hasattr(ankr_swap, "initial_A"),
        False,
        "Test pool",
        {"from": alice},
    )
    provider.set_address(0, registry, {"from": alice})
    yield registry


@given(new_ratio=strategy("uint256", min_value=1, max_value=10 ** 18 - 1))
def test_get_rates(alice, registry, registry_pool_info, new_ratio, ankr_swap):
    ankrETH[0].update_ratio(new_ratio, {"from": alice})

    rates = [0] * 8
    rates[0] = (10 ** 36) // new_ratio

    assert registry.get_rates(ankr_swap) == rates
    assert registry_pool_info.get_pool_info(ankr_swap)["rates"] == rates


def test_call_to_rate_calculator(alice, ankr_swap, registry, RateCalcMock):
    rate_calc = RateCalcMock[0]
    coin = ankrETH[0]
    tx = registry.get_rates.transact(ankr_swap, {"from": alice})

    expected = {
        "function": "get_rate(address)",
        "inputs": dict(_coin=coin.address),
        "op": "STATICCALL",
        "to": rate_calc.address,
    }
    assert all(tx.subcalls[0][k] == expected[k] for k in expected.keys())
