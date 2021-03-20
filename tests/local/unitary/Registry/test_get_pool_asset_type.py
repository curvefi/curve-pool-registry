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


@pytest.mark.once
def test_set_pool_asset_type(registry, alice, underlying_coins, swap):
    registry.set_pool_asset_type(swap, "USD", {"from": alice})

    assert registry.get_pool_asset_type(swap) == "USD"


@pytest.mark.once
def test_get_pool_asset_type_reverts_on_fail(registry, bob):
    with brownie.reverts("dev: admin-only function"):
        registry.set_pool_asset_type(ZERO_ADDRESS, "USD", {"from": bob})


@pytest.mark.once
def test_batch_set_pool_asset_type(registry, alice, underlying_coins, swap):
    asset_types = ["USD"] + [""] * 31
    asset_types = ["{0:32}".format(string) for string in asset_types]
    registry.batch_set_pool_asset_type(
        [swap] + [ZERO_ADDRESS] * 31, "".join(asset_types), {"from": alice}
    )

    assert registry.get_pool_asset_type(swap) == "{0:32}".format(
        "USD"
    )  # end user will need to strip text
