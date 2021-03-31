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
def registry(
    ERC20, Registry, RateCalc, provider, gauge_controller, alice, ankr_swap, lp_token, n_coins
):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})

    registry.add_pool(
        ankr_swap,
        1,
        ERC20.deploy("", "", 18, {"from": alice}),
        "0x71ca337d",
        pack_values([18]),
        pack_values([18]),
        hasattr(ankr_swap, "initial_A"),
        False,
        "",
        {"from": alice},
    )
    provider.set_address(0, registry, {"from": alice})
    yield registry


@pytest.mark.once
@given(new_ratio=strategy("uint256", min_value=1, max_value=10 ** 18 - 1))
def test_get_rates(alice, registry, registry_pool_info, new_ratio, ankr_swap):
    ankrETH[0].update_ratio(new_ratio, {"from": alice})

    rates = [0] * 8
    rates[0] = (10 ** 36) // new_ratio

    assert registry.get_rates(ankr_swap) == rates
    assert registry_pool_info.get_pool_info(ankr_swap)["rates"] == rates
