import requests
from brownie import Registry, Contract, accounts

from scripts.utils import pack_values, right_pad

GITHUB_POOLS = "https://api.github.com/repos/curvefi/curve-contract/contents/contracts/pools"
GITHUB_POOLDATA = "https://raw.githubusercontent.com/curvefi/curve-contract/master/contracts/pools/{}/pooldata.json"

DEPLOYER = accounts[0]
REGISTRY = ""

RATE_METHOD_IDS = {
    "cERC20": "0x182df0f5",     # exchangeRateStored
    "renERC20": "0xbd6d894d",   # exchangeRateCurrent
    "yERC20": "0x77c7b8fc",     # getPricePerFullShare
}

def main(registry=REGISTRY, deployer=DEPLOYER):
    if registry:
        registry = Contract(registry)
    else:
        registry = Registry.deploy("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB", {'from': deployer})

    print("Querying Github for pool deployments...")
    pool_data = {}
    pool_names = [i['name'] for i in requests.get(GITHUB_POOLS).json() if i['type'] == "dir"]

    for name in pool_names:
        data = requests.get(GITHUB_POOLDATA.format(name)).json()
        if "swap_address" not in data:
            print(f"Cannot add {name} - no deployment address!")
            continue
        pool_data[name] = data

    for name, data in pool_data.items():
        if registry.get_n_coins(data['swap_address'])[0] != 0:
            print(f"{name} has already been added - skipping")
            continue
        print(f"Adding {name}...")

        swap = Contract(data['swap_address'])
        token = data['lp_token_address']
        n_coins = len(data['coins'])
        decimals = pack_values([i['decimals'] for i in data['coins']])

        if "base_pool" in data:
            # adding a metapool
            base_n_coins = len(pool_data[data['base_pool']]['coins'])
            registry.add_metapool(swap, n_coins, base_n_coins, token, decimals, {'from': deployer})
            continue

        is_v1 = data['lp_contract'] == "CurveTokenV1"
        has_initial_A = hasattr(swap, 'intitial_A')
        rate_method_id = "0x00"
        if "wrapped_contract" in data:
            rate_method_id = RATE_METHOD_IDS[data['wrapped_contract']]
        rate_method_id = right_pad(rate_method_id)

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
                {'from': deployer}
            )
        else:
            use_lending_rates = pack_values([i['wrapped'] for i in data['coins']])
            registry.add_pool_without_underlying(
                swap,
                n_coins,
                token,
                rate_method_id,
                decimals,
                use_lending_rates,
                has_initial_A,
                is_v1,
                {'from': deployer}
            )
