# @version 0.1.0

MAX_COINS: constant(int128) = 7

struct AddressArray:
    length: int128
    addresses: address[65536]

struct PoolArray:
    location: int128
    coins: address[MAX_COINS]

contract CurvePool:
    def coins(i: int128) -> address: constant

admin: address

pool_list: address[65536]   # master list of pools
pool_count: public(int128)  # actual length of pool_list

pool_data: map(address, PoolArray)   # data for specific pools
markets: map(address, AddressArray)  # list of pools where a token is tradeable


@public
def __init__():
    self.admin = msg.sender


@public
def add_pool(_pool: address, _n_coins: int128) -> bool:
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    # add pool to pool_list
    _length: int128 = self.pool_count
    self.pool_list[_length] = _pool
    self.pool_count = _length + 1
    self.pool_data[_pool].location = _length

    for i in range(MAX_COINS):
        if i == _n_coins:
            break

        # add coin address to pool_data
        _coin: address = CurvePool(_pool).coins(i)
        self.pool_data[_pool].coins[i] = _coin

        # add pool address to markets
        _length = self.markets[_coin].length
        self.markets[_coin].addresses[_length] = _pool
        self.markets[_coin].length = _length + 1

    return True
