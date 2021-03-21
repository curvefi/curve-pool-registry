import pytest
from brownie import ankrETH, aToken
from brownie.test import given, strategy

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def coins(alice, ERC20NoReturn):
    coins = []
    for i in range(3):
        contract = alice.deploy(ERC20NoReturn, "", "", 18)
        coins.append(contract)
    coins.append("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE")
    return coins


@pytest.fixture(scope="module")
def aave_wrapped_coins(alice, coins):
    wrapped_coins = []
    for i, (coin, decimals) in enumerate(zip(coins, len(coins) * [18])):
        if coin == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
            wrapped_coins.append(coin)
            continue
        contract = aToken.deploy(
            f"Wrapped Test Token {i}", f"wTST{i}", decimals, coin, 10 ** 18, {"from": alice}
        )
        wrapped_coins.append(contract)

    return wrapped_coins


@pytest.fixture(scope="module")
def aave_swap(PoolMockV2, alice, aave_wrapped_coins, coins):
    n_coins = len(coins)
    wrapped_coins = aave_wrapped_coins + [ZERO_ADDRESS] * (4 - len(aave_wrapped_coins))
    underlying_coins = coins + [ZERO_ADDRESS] * (4 - len(coins))

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
    RateCalc,
    provider,
    gauge_controller,
    alice,
    aave_swap,
    ankr_swap,
    lp_token,
    n_coins,
):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    rate_calc = alice.deploy(RateCalc)

    registry.add_pool(
        aave_swap,
        n_coins,
        lp_token,
        "0x00",
        pack_values([18] * 3),
        pack_values([18] * 3),
        hasattr(aave_swap, "initial_A"),
        False,
        "",
        {"from": alice},
    )
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
    for _ in range(4):
        provider.add_new_id(rate_calc, "", {"from": alice})
    yield registry


@pytest.mark.once
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
