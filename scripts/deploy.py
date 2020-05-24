import json
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy
from brownie import web3, accounts, Registry, yERC20, cERC20

DEPLOYER = "0xC447FcAF1dEf19A583F97b3620627BF69c05b5fB"
POA = True
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TETHERS = ["0xdAC17F958D2ee523a2206206994597C13D831ec7"] + [ZERO_ADDRESS] * 3
MAX_COINS = 8
EMPTY_DECIMALS = [0] * MAX_COINS

POOLS = [
        (  # Compound
            '0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56', 2, '0x845838DF265Dcd2c412A1Dc9e959c7d08537f8a2',
            cERC20.signatures['exchangeRateStored'], EMPTY_DECIMALS, EMPTY_DECIMALS,
        ),
        (  # USDT
            '0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C', 3, '0x9fC689CCaDa600B6DF723D9E47D84d76664a1F23',
            cERC20.signatures['exchangeRateStored'], EMPTY_DECIMALS, EMPTY_DECIMALS,
        ),
        (  # Y
            '0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51', 4, '0xdF5e0e81Dff6FAF3A7e52BA697820c5e32D806A8',
            yERC20.signatures['getPricePerFullShare'], EMPTY_DECIMALS, EMPTY_DECIMALS,
        ),
        (  # BUSD
            '0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27', 4, '0x3B3Ac5386837Dc563660FB6a0937DFAa5924333B',
            yERC20.signatures['getPricePerFullShare'], EMPTY_DECIMALS, EMPTY_DECIMALS,
        ),
        (  # SUSD
            '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD', 4, '0xC25a3A3b969415c80451098fa907EC722572917F',
            b'\x00' * 4, EMPTY_DECIMALS, EMPTY_DECIMALS,
        ),
        (  # PAX
            '0x06364f10B501e868329afBc005b3492902d6C763', 4, '0xD905e2eaeBe188fc92179b6350807D8bd91Db0D8',
            yERC20.signatures['getPricePerFullShare'], EMPTY_DECIMALS, EMPTY_DECIMALS
        ),
        (  # RenBTC
            '0x8474c1236F0Bc23830A23a41aBB81B2764bA9f4F', 2, '0x7771F704490F9C0C3B06aFe8960dBB6c58CBC812',
            cERC20.signatures['exchangeRateCurrent'], EMPTY_DECIMALS, [True] + [False] * 7
        ),
]


def main(deployment_address=DEPLOYER):
    deployer = accounts.at(deployment_address) if deployment_address else accounts[1]

    web3.eth.setGasPriceStrategy(gas_strategy)
    web3.middleware_onion.add(middleware.time_based_cache_middleware)
    web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    web3.middleware_onion.add(middleware.simple_cache_middleware)
    if POA:
        web3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)

    while True:
        try:
            registry = Registry.deploy(TETHERS, {'from': deployer})
        except KeyError:
            continue
        break
    with open('registry.abi', 'w') as f:
        json.dump(registry.abi, f, indent=True)

    for i, pool in enumerate(POOLS):
        print("Adding pool {} out of {}...".format(i + 1, len(POOLS)))
        args = list(pool) + [{'from': deployer}]
        while True:
            try:
                if isinstance(args[-1][0], bool):
                    # if the last arg is a bool array, call `add_pool_without_underlying`
                    registry.add_pool_without_underlying(*args)
                else:
                    # otherwise, call `add_pool`
                    registry.add_pool(*args)
            except KeyError:
                continue
            break
