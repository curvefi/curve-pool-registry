# curve-pool-registry

Registry smart contract for [Curve.fi](https://github.com/curvefi/curve-contract) pools.

## Usage

Use the following functions to interact with this contract.

### Finding Curve Pools

```python
def pool_count() -> int128: view
def pool_list(i: int128) -> address: view
```

* `pool_count` provides the number of pools currently included in the registry.
* You may call to `pool_list` to obtain the address for a specific pool.

Calling with a value greater than `pool_count` will return a zero value.

```python
def find_pool_for_coins(from: address, to: address, i: uint256 = 0) -> address: view
```

Locate a pool based on the tokens you wish to trade.

* `from`: Address of the token you wish to sell
* `to`: Address of the token you wish to buy
* `i`: Optional index value - if more than one pool is available for the trade, use this argument to see the n-th result

Returns a zero value if no pool is available, or `i` exceeds the number of available pools.

### Getting Pool Information

Arrays will always have a length of 7. Trailing zero values should be ignored.

```python
def get_pool_coins(pool: address) -> (address[8], address[8], uint256[8]): view
```

Get information on tradeable tokens in a pool.

Returns arrays of token addresses, underlying token addresses, and underlying token decimals.

```python
def get_pool_info(pool: address) -> (uint256[8], uint256[8], uint256[8], uint256, uint256): view
```

Get information on a pool.

Returns token balances, underlying token balances, underlying token decimals, pool amplification coefficient, pool fees.

If the pool does not exist the call will revert.

```python
def get_pool_rates(pool: address) -> uint256[8]: view
```

Get rates between tokens and underlying tokens.

For tokens where there is no underlying tokens, or where the underlying token cannot be swapped, the rate is given as `1e18`.

### Making Trades

```python
def get_exchange_amount(pool: address, from: address, to: address, amount: uint256) -> uint256: view
```

Get the number of tokens that will be received in an exchange.

* `pool`: Pool address
* `from`: Address of the token you intend to sell
* `to`: Address of the token you intend to buy
* `amount`: Quantity of `from` to be sent in the exchange

Returns the expected amount of `to` to be received in the exchange, after fees.

```python
def exchange(pool: address, from: address, to: address, amount: uint256, expected: uint256) -> bool: payable
```

Perform a token exchange.

* `pool`: Pool address
* `from`: Address of the token you intend to sell
* `to`: Address of the token you intend to buy
* `amount`: Quantity of `from` to be sent in the exchange
* `expected`: Minimum quantity of tokens received in order for the transaction to succeed

Prior to calling this function you must call the `approve` method in `from`, authrorizing the registry contract to transfer `amount` tokens.

## Testing and Development

This project is written for compilation with Vyper [`0.2.3`](https://github.com/vyperlang/vyper/releases/tag/v0.2.3).

Unit testing and development of this project is performed using [Brownie](https://github.com/iamdefinitelyahuman/brownie).

To get started, first create and initialize a Python [virtual environment](https://docs.python.org/3/library/venv.html). Next, install the requirements:

```bash
pip install -r requirements
```

You can then run the test suite:

```bash
brownie test
```

## License

This project is licensed under the [MIT](LICENSE) license.
