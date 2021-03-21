import pytest


@pytest.fixture(scope="module", autouse=True)
def add_addresses_provider(
    alice, provider, calculator, registry, registry_pool_info, registry_swap, rate_calc
):
    provider.set_address(0, registry, {"from": alice})
    provider.add_new_id(registry_pool_info, "PoolInfo Getters", {"from": alice})  # 1
    provider.add_new_id(registry_swap, "Generalized Swap contract", {"from": alice})  # 2
    provider.add_new_id(registry_swap, "", {"from": alice})  # 3 - dummy should be metapool factory
    provider.add_new_id(rate_calc, "Curve Coin Rate Calculator", {"from": alice})
