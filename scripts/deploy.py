from brownie import ZERO_ADDRESS, AddressProvider, PoolInfo, Registry, Swaps, accounts
from brownie.network.gas.strategies import GasNowScalingStrategy

from scripts.add_pools import main as add_pools

# modify this prior to mainnet use
deployer = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)

ADDRESS_PROVIDER = "0x0000000022D53366457F9d5E68Ec105046FC4383"
GAUGE_CONTROLLER = "0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB"

gas_strategy = GasNowScalingStrategy("standard", "fast")


def deploy_registry():
    """
    Deploy `Registry`, add all current pools, and set the address in `AddressProvider`.
    """
    balance = deployer.balance()

    provider = AddressProvider.at(ADDRESS_PROVIDER)
    registry = Registry.deploy(
        ADDRESS_PROVIDER,
        GAUGE_CONTROLLER,
        {'from': deployer, 'gas_price': gas_strategy}
    )
    add_pools(registry, deployer)
    provider.set_address(0, registry, {'from': deployer, 'gas_price': gas_strategy})

    print(f"Registry deployed to: {registry.address}")
    print(f"Total gas used: {(balance - deployer.balance()) / 1e18:.4f} eth")


def deploy_pool_info():
    """
    Deploy `PoolInfo` and set the address in `AddressProvider`.
    """
    balance = deployer.balance()

    provider = AddressProvider.at(ADDRESS_PROVIDER)

    pool_info = PoolInfo.deploy(provider, {'from': deployer, 'gas_price': gas_strategy})

    if provider.max_id() == 0:
        provider.add_new_id(
            pool_info,
            "PoolInfo Getters",
            {'from': deployer, 'gas_price': gas_strategy}
        )
    else:
        provider.set_address(1, pool_info, {'from': deployer, 'gas_price': gas_strategy})

    print(f"PoolInfo deployed to: {pool_info.address}")
    print(f"Total gas used: {(balance - deployer.balance()) / 1e18:.4f} eth")


def deploy_swaps():
    """
    Deploy `Swaps` and set the address in `AddressProvider`.
    """
    balance = deployer.balance()

    provider = AddressProvider.at(ADDRESS_PROVIDER)

    swaps = Swaps.deploy(provider, ZERO_ADDRESS, {'from': deployer, 'gas_price': gas_strategy})

    if provider.max_id() == 1:
        provider.add_new_id(
            swaps,
            "Exchanges",
            {'from': deployer, 'gas_price': gas_strategy}
        )
    else:
        provider.set_address(2, swaps, {'from': deployer, 'gas_price': gas_strategy})

    print(f"PoolInfo deployed to: {swaps.address}")
    print(f"Total gas used: {(balance - deployer.balance()) / 1e18:.4f} eth")
