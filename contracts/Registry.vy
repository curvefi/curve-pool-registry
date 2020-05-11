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
