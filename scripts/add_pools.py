import requests
from brownie import Registry, Contract, accounts

from scripts.get_pool_data import get_pool_data
from scripts.utils import get_gas_price, pack_values

# modify this prior to mainnet use
DEPLOYER = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)
REGISTRY = "0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c"

GITHUB_POOLS = "https://api.github.com/repos/curvefi/curve-contract/contents/contracts/pools"
GITHUB_POOLDATA = "https://raw.githubusercontent.com/curvefi/curve-contract/master/contracts/pools/{}/pooldata.json"

RATE_METHOD_IDS = {
    "cERC20": "0x182df0f5",     # exchangeRateStored
    "renERC20": "0xbd6d894d",   # exchangeRateCurrent
    "yERC20": "0x77c7b8fc",     # getPricePerFullShare
}


def add_pool(data, registry, deployer):
    swap = Contract(data['swap_address'])
    token = data['lp_token_address']
    n_coins = len(data['coins'])
    decimals = pack_values([i.get('decimals', i.get('wrapped_decimals')) for i in data['coins']])

    if "base_pool" in data:
        # adding a metapool
        registry.add_metapool(
            swap,
            n_coins,
            token,
            decimals,
            {'from': deployer, 'gas_price': get_gas_price()}
        )
        return

    is_v1 = data['lp_contract'] == "CurveTokenV1"
    has_initial_A = hasattr(swap, 'intitial_A')
    rate_method_id = "0x00"
    if "wrapped_contract" in data:
        rate_method_id = RATE_METHOD_IDS[data['wrapped_contract']]

    if hasattr(swap, 'exchange_underlying'):
        wrapped_decimals = pack_values([i.get('wrapped_decimals', i['decimals']) for i in data['coins']])
        registry.add_pool(
            swap,
            n_coins,
            token,
            rate_method_id,
            wrapped_decimals,
            decimals,
            has_initial_A,
            is_v1,
            {'from': deployer, 'gas_price': get_gas_price()}
        )
    else:
        use_lending_rates = pack_values(["wrapped_decimals" in i for i in data['coins']])
        registry.add_pool_without_underlying(
            swap,
            n_coins,
            token,
            rate_method_id,
            decimals,
            use_lending_rates,
            has_initial_A,
            is_v1,
            {'from': deployer, 'gas_price': get_gas_price()}
        )


def main(registry=REGISTRY, deployer=DEPLOYER):
    """
    Fetch pool data from Github and add new pools to the existing registry deployment.
    """
    registry = Registry.at(registry)
    pool_data = get_pool_data(True)

    print("Adding pools to registry...")

    for name, data in pool_data.items():
        if registry.get_n_coins(data['swap_address'])[0] != 0:
            print(f"{name} has already been added - skipping")
            continue

        print(f"Adding {name}...")
        add_pool(data, registry, deployer)
