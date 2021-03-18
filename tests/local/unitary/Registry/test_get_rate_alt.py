import pytest
from brownie import ankrETH, aToken
from brownie.test import given, strategy

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def aave_wrapped_coins(_underlying_coins, _wrapped_decimals, alice, n_coins):
    coins = []
    for i, (coin, decimals) in enumerate(zip(_underlying_coins, _wrapped_decimals)):
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            coins.append(coin)
            continue
        contract = aToken.deploy(
            f"Wrapped Test Token {i}", f"wTST{i}", decimals, coin, 10 ** 18, {"from": alice}
        )
        coins.append(contract)

    return coins[:n_coins]


@pytest.fixture(scope="module")
def aave_wrapped_decimals(_wrapped_decimals, n_coins):
    return _wrapped_decimals[:n_coins]


@pytest.fixture(scope="module")
def aave_swap(PoolMockV2, alice, aave_wrapped_coins, underlying_coins):
    n_coins = len(underlying_coins)
    wrapped_coins = aave_wrapped_coins + [ZERO_ADDRESS] * (4 - len(aave_wrapped_coins))
    underlying_coins = underlying_coins + [ZERO_ADDRESS] * (4 - len(underlying_coins))

    contract = PoolMockV2.deploy(
        n_coins, wrapped_coins, underlying_coins, 70, 4000000, {"from": alice}
    )
    return contract


@pytest.fixture(scope="module")
def ankr_swap(PoolMockV2, alice):
    underlying_coins = ["0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"]
    wrapped_coins = [ankrETH.deploy({"from": alice})] + [ZERO_ADDRESS] * 3
    underlying_coins = underlying_coins + [ZERO_ADDRESS] * 3

    contract = PoolMockV2.deploy(1, wrapped_coins, underlying_coins, 70, 4000000, {"from": alice})
    return contract


@pytest.fixture(scope="module")
def registry(
    ERC20,
    Registry,
    provider,
    gauge_controller,
    alice,
    aave_swap,
    ankr_swap,
    lp_token,
    n_coins,
    underlying_decimals,
    aave_wrapped_decimals,
):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    registry.add_pool(
        aave_swap,
        n_coins,
        lp_token,
        "0x4e4e197d",
        pack_values(aave_wrapped_decimals),
        pack_values(underlying_decimals),
        hasattr(aave_swap, "initial_A"),
        False,
        {"from": alice},
    )
    registry.add_pool(
        ankr_swap,
        1,
        ERC20.deploy("", "", 18, {"from": alice}),
        "0x267bee12",
        pack_values([18]),
        pack_values([18]),
        hasattr(ankr_swap, "initial_A"),
        False,
        {"from": alice},
    )
    provider.set_address(0, registry, {"from": alice})
    yield registry


def test_get_rates_aave(registry, registry_pool_info, aave_swap, aave_wrapped_coins):
    rates = [10 ** 18] * len(aave_wrapped_coins)
    rates += [0] * (8 - len(rates))

    assert registry.get_rates(aave_swap) == rates
    assert registry_pool_info.get_pool_info(aave_swap)["rates"] == rates


@pytest.mark.once
@given(new_ratio=strategy("uint256", min_value=1, max_value=10 ** 18 - 1))
def test_get_rates(alice, registry, registry_pool_info, new_ratio, ankr_swap):
    ankrETH[0].update_ratio(new_ratio, {"from": alice})

    rates = [0] * 8
    rates[0] = (10 ** 36) // new_ratio

    assert registry.get_rates(ankr_swap) == rates
    assert registry_pool_info.get_pool_info(ankr_swap)["rates"] == rates
