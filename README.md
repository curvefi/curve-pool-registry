# curve-pool-registry

On-chain registry and unified API for [Curve.fi](https://github.com/curvefi/curve-contract) pools.

## Usage

See the [documentation](https://curve.readthedocs.io/) for information on how this project is organized, and how it may be integrated within other projects.

## Deployments

* [`AddressProvider`](contracts/AddressProvider.vy): [0x0000000022D53366457F9d5E68Ec105046FC4383](https://etherscan.io/address/0x0000000022d53366457f9d5e68ec105046fc4383)
* [`Registry`](contracts/Registry.vy): [0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c](https://etherscan.io/address/0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c)
* [`PoolInfo`](contracts/PoolInfo.vy): [0xe64608E223433E8a03a1DaaeFD8Cb638C14B552C](https://etherscan.io/address/0xe64608E223433E8a03a1DaaeFD8Cb638C14B552C)

## Testing and Development

### Dependencies

* [python3](https://www.python.org/downloads/release/python-368/) version 3.6 or greater, python3-dev
* [brownie](https://github.com/iamdefinitelyahuman/brownie) - tested with version [1.13.0](https://github.com/eth-brownie/brownie/releases/tag/v1.13.0)
* [ganache-cli](https://github.com/trufflesuite/ganache-cli) - tested with version [6.12.1](https://github.com/trufflesuite/ganache-cli/releases/tag/v6.12.1)

Curve contracts are compiled using [Vyper](https://github.com/vyperlang/vyper), however installation of the required Vyper versions is handled by Brownie.

### Setup

To get started, first create and initialize a Python [virtual environment](https://docs.python.org/3/library/venv.html). Next, clone the repo and install the developer dependencies:

```bash
git clone https://github.com/curvefi/curve-pool-registry.git
cd curve-pool-registry
pip install -r requirements.txt
```

### Running the Tests

The registry has two independent test suites.

#### Local tests

The [local test suite](tests/local) is designed to be run in a local environment. It is mostly comprised of parametrized unit tests that validate functionality against many possible pool iterations.

To run the entire local test suite:

```bash
brownie test tests/local
```

You can optionally include the `--once` flag to skip parametrization and run each test exactly once.

#### Forked tests

The [forked test suite](tests/forked) is designed for use with a forked mainnet. These tests verify functionality within the registry against actual data from deployed pools.  The data is obtained from the [`pooldata.json`](https://github.com/curvefi/curve-contract/tree/master/contracts/pools#adding-a-new-pool) file within each subdirectory in [`curvefi/curve-contract/contract/pools`](https://github.com/curvefi/curve-contract/tree/master/contracts/pools).


To run the forked tests:

```bash
brownie test tests/forked
```

You can optionally include the `--pool` flag to only target one or more specific pools:

```bash
brownie test tests/forked --pool 3pool,gusd
```

## Deployment

Deployment is handled via functions within [`scripts/deploy.py`](scripts/deploy.py).

To run a deployment function:

```bash
brownie run deploy [FUNCTION NAME] --network mainnet
```

You must set `deployer` prior to running on the mainnet. It is recommended to test the script in a forked mainnet environment prior to actual deployment.

## License

Except where otherwise noted, (c) Curve.Fi, 2020 - [All rights reserved](LICENSE).
