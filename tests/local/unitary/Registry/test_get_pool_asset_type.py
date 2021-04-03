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
def test_set_pool_asset_type(registry, alice, swap):
    tx = registry.set_pool_asset_type(swap, 42, {"from": alice})

    assert registry.get_pool_asset_type(swap) == 42
    assert registry.last_updated() == tx.timestamp


@pytest.mark.once
def test_get_pool_asset_type_reverts_on_fail(registry, bob):
    with brownie.reverts("dev: admin-only function"):
        registry.set_pool_asset_type(ZERO_ADDRESS, 42, {"from": bob})


@pytest.mark.once
def test_batch_set_pool_asset_type(registry, alice, swap):
    asset_types = [42] + [0] * 31
    tx = registry.batch_set_pool_asset_type(
        [swap] + [ZERO_ADDRESS] * 31, asset_types, {"from": alice}
    )

    assert registry.get_pool_asset_type(swap) == 42
    assert registry.last_updated() == tx.timestamp


@pytest.mark.once
def test_asset_type_removed_after_pool_removal(registry, swap, alice):
    registry.set_pool_asset_type(swap, 42, {"from": alice})
    registry.remove_pool(swap, {"from": alice})

    assert registry.get_pool_asset_type(swap) == 0
