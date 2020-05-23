import json
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy
from brownie import web3, accounts, Registry, yERC20, cERC20

DEPLOYER = "0xC447FcAF1dEf19A583F97b3620627BF69c05b5fB"
POA = True
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TETHERS = ["0xdAC17F958D2ee523a2206206994597C13D831ec7"] + [ZERO_ADDRESS] * 3
MAX_COINS = 8

POOLS = [
        (  # Compound
            '0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56', 2, '0x845838DF265Dcd2c412A1Dc9e959c7d08537f8a2',
            [0] * MAX_COINS, cERC20.signatures['exchangeRateStored']
        ),
        (  # USDT
            '0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C', 3, '0x9fC689CCaDa600B6DF723D9E47D84d76664a1F23',
            [0] * MAX_COINS, cERC20.signatures['exchangeRateStored']
        ),
        (  # Y
            '0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51', 4, '0xdF5e0e81Dff6FAF3A7e52BA697820c5e32D806A8',
            [0] * MAX_COINS, yERC20.signatures['getPricePerFullShare']
        ),
        (  # BUSD
            '0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27', 4, '0x3B3Ac5386837Dc563660FB6a0937DFAa5924333B',
            [0] * MAX_COINS, yERC20.signatures['getPricePerFullShare']
        ),
        (  # SUSD
            '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD', 4, '0xC25a3A3b969415c80451098fa907EC722572917F',
            [0] * MAX_COINS, b'\x00' * 4
        ),
        (  # PAX
            '0x06364f10B501e868329afBc005b3492902d6C763', 4, '0xD905e2eaeBe188fc92179b6350807D8bd91Db0D8',
            [0] * MAX_COINS, yERC20.signatures['getPricePerFullShare']
        ),
        (  # RenBTC
            '0x8474c1236F0Bc23830A23a41aBB81B2764bA9f4F', 2, '0x7771F704490F9C0C3B06aFe8960dBB6c58CBC812',
            [0] * MAX_COINS, cERC20.signatures['exchangeRateCurrent'],
            False, [True] + [False] * 7
        ),
]

# For tests XXX (alpha)
POOLS = [POOLS[-1]]


def main():
    deployer = accounts.at(DEPLOYER) if DEPLOYER else accounts[1]

    web3.eth.setGasPriceStrategy(gas_strategy)
    web3.middleware_onion.add(middleware.time_based_cache_middleware)
    web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    web3.middleware_onion.add(middleware.simple_cache_middleware)
    if POA:
        web3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)

    registry = Registry.deploy(TETHERS, {'from': deployer})
    registry.set_alias('registry-alpha')
    with open('registry.abi', 'w') as f:
        json.dump(registry.abi, f, indent=True)

    for pool in POOLS:
        args = list(pool) + [{'from': deployer}]
        registry.add_pool(*args)
