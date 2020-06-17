import json
from web3 import middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy as gas_strategy
from brownie import web3, accounts, Registry, yERC20, cERC20, CurveCalc
# from brownie import Contract

from scripts.utils import pack_values, right_pad

DEPLOYER = accounts[0]  # TEST
# DEPLOYER = "0xC447FcAF1dEf19A583F97b3620627BF69c05b5fB"
POA = False
USE_MIDDLEWARE = False
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TETHERS = ["0xdAC17F958D2ee523a2206206994597C13D831ec7"] + [ZERO_ADDRESS] * 3
MAX_COINS = 8
EMPTY_DECIMALS = pack_values([0] * MAX_COINS)


def insert_calculator(params, calculator):
    return params[:3] + (calculator.address,) + params[3:]


POOLS = [
    (  # Compound
        '0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56', 2, '0x845838DF265Dcd2c412A1Dc9e959c7d08537f8a2',
        right_pad(cERC20.signatures['exchangeRateStored']), EMPTY_DECIMALS, EMPTY_DECIMALS,
    ),
    (  # USDT
        '0x52EA46506B9CC5Ef470C5bf89f17Dc28bB35D85C', 3, '0x9fC689CCaDa600B6DF723D9E47D84d76664a1F23',
        right_pad(cERC20.signatures['exchangeRateStored']), EMPTY_DECIMALS, EMPTY_DECIMALS,
    ),
    (  # Y
        '0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51', 4, '0xdF5e0e81Dff6FAF3A7e52BA697820c5e32D806A8',
        right_pad(yERC20.signatures['getPricePerFullShare']), EMPTY_DECIMALS, EMPTY_DECIMALS,
    ),
    (  # BUSD
        '0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27', 4, '0x3B3Ac5386837Dc563660FB6a0937DFAa5924333B',
        right_pad(yERC20.signatures['getPricePerFullShare']), EMPTY_DECIMALS, EMPTY_DECIMALS,
    ),
    (  # SUSD
        '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD', 4, '0xC25a3A3b969415c80451098fa907EC722572917F',
        "0x00", EMPTY_DECIMALS, EMPTY_DECIMALS,
    ),
    (  # PAX
        '0x06364f10B501e868329afBc005b3492902d6C763', 4, '0xD905e2eaeBe188fc92179b6350807D8bd91Db0D8',
        right_pad(yERC20.signatures['getPricePerFullShare']), EMPTY_DECIMALS, EMPTY_DECIMALS
    ),
]

POOLS_NO_UNDERLYING = [
    (  # RenBTC
        '0x93054188d876f558f4a66B2EF1d97d16eDf0895B', 2, '0x49849C98ae39Fff122806C06791Fa73784FB3675',
        right_pad(cERC20.signatures['exchangeRateCurrent']), EMPTY_DECIMALS, pack_values([True] + [False] * 7)
    ),
    (  # SBTC
        '0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714', 3, '0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3',
        right_pad(cERC20.signatures['exchangeRateCurrent']), EMPTY_DECIMALS, pack_values([True] + [False] * 7)
    ),
]

GAS_PRICES_COINS = {
    '0x6B175474E89094C44Da98b954EedeAC495271d0F': 23000,  # DAI
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 27000,  # USDC
    '0xdAC17F958D2ee523a2206206994597C13D831ec7': 20000,  # USDT
    '0x57Ab1ec28D129707052df4dF418D58a2D46d5f51': 100000,  # SUSD
    '0x0000000000085d4780B73119b644AE5ecd22b376': 30700,  # TUSD
    '0x4Fabb145d64652a948d72533023f6E7A623C7C53': 58000,  # BUSD
    '0x8E870D67F660D95d5be530380D0eC0bd388289E1': 21500,  # PAX
    '0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D': 25000,  # renBTC
    '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599': 24000,  # wBTC
    '0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643': 40000,  # cDAI
    '0x39AA39c021dfbaE8faC545936693aC917d5E7563': 24000,  # cUSDC
    '0x16de59092dAE5CcF4A1E6439D611fd0653f0Bd01': 24000,  # yDAI
    '0xd6aD7a6750A7593E092a9B218d66C0A814a3436e': 24000,  # yUSDC
    '0x83f798e925BcD4017Eb265844FDDAbb448f1707D': 24000,  # yUSDT
    '0x73a052500105205d34Daf004eAb301916DA8190f': 24000,  # yTUSD
    '0xC2cB1040220768554cf699b0d863A3cd4324ce32': 24000,  # ybDAI
    '0x26EA744E5B887E5205727f55dFBE8685e3b21951': 24000,  # ybUSDC
    '0xE6354ed5bC4b393a5Aad09f21c46E101e692d447': 24000,  # ybUSDT
    '0x04bC0Ab673d88aE9dbC9DA2380cB6B79C4BCa9aE': 24000,  # ybBUSD
    '0x99d1Fa417f94dcD62BfE781a1213c092a47041Bc': 24000,  # ycDAI
    '0x9777d7E2b60bB01759D0E2f8be2095df444cb07E': 24000,  # ycUSDC
    '0x1bE5d71F2dA660BFdee8012dDc58D024448A0A59': 24000,  # ycUSDT
}
GAS_PRICES_POOLS = {
    '0xA2B47E3D5c44877cca798226B7B8118F9BFb7A56': (260000, 655000),  # Compound
    '0x06364f10B501e868329afBc005b3492902d6C763': (337000, 706000),  # PAX
    '0x45F783CCE6B7FF23B2ab2D70e416cdb7D6055f51': (337000, 756000),  # Y
    '0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27': (337000, 706000),  # BUSD
    '0xA5407eAE9Ba41422680e2e00537571bcC53efBfD': (83000, 83000),  # SUSD
    '0x93054188d876f558f4a66B2EF1d97d16eDf0895B': (79000, 79000),  # Ren
    '0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714': (79000, 79000),  # sRen
}


def main(deployment_address=DEPLOYER):
    deployer = accounts.at(deployment_address) if deployment_address else accounts[1]

    if USE_MIDDLEWARE:
        web3.eth.setGasPriceStrategy(gas_strategy)
        web3.middleware_onion.add(middleware.time_based_cache_middleware)
        web3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
        web3.middleware_onion.add(middleware.simple_cache_middleware)
    if POA:
        web3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)

    # try:
    #     registry = Contract("0x2eD8727881A07bB8192C94D1a21ac827d22Fc25C")
    #     print("Using saved registry")
    # except Exception:
    while True:
        try:
            registry = Registry.deploy(TETHERS, {'from': deployer})
        except KeyError:
            continue
        break
    with open('registry.abi', 'w') as f:
        json.dump(registry.abi, f, indent=True)

    while True:
        try:
            calculator = CurveCalc.deploy({'from': deployer})
        except KeyError:
            continue
        break
    with open('calculator.abi', 'w') as f:
        json.dump(calculator.abi, f, indent=True)

    pools = POOLS
    pools = [insert_calculator(p, calculator) for p in pools]

    pools_no_underlying = POOLS_NO_UNDERLYING
    pools_no_underlying = [insert_calculator(p, calculator) for p in pools_no_underlying]

    length = len(pools) + len(pools_no_underlying)
    for i, pool in enumerate(pools + pools_no_underlying, start=1):
        print(f"Adding pool {i} out of {length}...")
        args = list(pool) + [{'from': deployer}]
        while True:
            try:
                if pool in pools:
                    registry.add_pool(*args)
                elif pool in pools_no_underlying:
                    registry.add_pool_without_underlying(*args)
                else:
                    raise RuntimeError("Something weird happened.")
            except (KeyError, ValueError):
                continue
            break

    gas_prices_coins = list(GAS_PRICES_COINS.items())
    gas_prices_pools = list(GAS_PRICES_POOLS.items())

    for i in range(0, len(gas_prices_coins), 10):
        chunk = gas_prices_coins[i:(i + 10)]
        chunk += [(ZERO_ADDRESS, 0)] * (10 - len(chunk))
        addrs, gas = list(zip(*chunk))
        registry.set_coin_gas_estimates(addrs, gas, {'from': deployer})

    for i in range(0, len(gas_prices_pools), 5):
        chunk = gas_prices_pools[i:(i + 5)]
        chunk += [(ZERO_ADDRESS, (0, 0))] * (5 - len(chunk))
        addrs, gas = list(zip(*chunk))
        registry.set_pool_gas_estimates(addrs, gas, {'from': deployer})
