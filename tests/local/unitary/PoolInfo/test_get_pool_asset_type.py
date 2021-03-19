import brownie
import pytest

from scripts.utils import pack_values

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(autouse=True)
def setup(registry, alice, swap, lp_token, n_coins, is_v1, underlying_decimals):
    registry.add_pool_without_underlying(
        swap,
        n_coins,
        lp_token,
        "0x00",
        pack_values(underlying_decimals),
        0,  # use rates
        hasattr(swap, "initial_A"),
        is_v1,
        "Base Swap",
        {"from": alice},
    )
    yield registry


@pytest.mark.once
def test_set_pool_asset_type(registry_pool_info, alice, underlying_coins, swap):
    registry_pool_info.set_pool_asset_type(swap, "USD", {"from": alice})

    assert registry_pool_info.get_pool_asset_type(swap) == "USD"


@pytest.mark.once
def test_get_pool_asset_type_reverts_on_fail(registry_pool_info, bob):
    with brownie.reverts("dev: admin-only function"):
        registry_pool_info.set_pool_asset_type(ZERO_ADDRESS, "USD", {"from": bob})
