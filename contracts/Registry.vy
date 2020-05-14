# @version 0.1.0

from vyper.interfaces import ERC20

MAX_COINS: constant(int128) = 7

struct AddressArray:
    length: int128
    addresses: address[65536]

struct PoolArray:
    location: int128
    coins: address[MAX_COINS]
    underlying_coins: address[MAX_COINS]

contract CurvePool:
    def A() -> uint256: constant
    def fee() -> uint256: constant
    def coins(i: int128) -> address: constant
    def underlying_coins(i: int128) -> address: constant
    def get_dy(i: int128, j: int128, dx: uint256) -> uint256: constant
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): modifying
    def exchange_underlying(i: int128, j: int128, dx: uint256, min_dy: uint256): modifying


admin: address

pool_list: public(address[65536])   # master list of pools
pool_count: public(int128)  # actual length of pool_list

pool_data: map(address, PoolArray)   # data for specific pools
markets: map(address, AddressArray)  # list of pools where a token is tradeable
underlying_markets: map(address, AddressArray)  # list of pools where a token is tradeable


@public
def __init__():
    self.admin = msg.sender


@private
def _add_pool_to_market(_coin: address, _pool: address):
    _length: int128 = self.markets[_coin].length
    self.markets[_coin].addresses[_length] = _pool
    self.markets[_coin].length = _length + 1



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

        # add coin
        _coin: address = CurvePool(_pool).coins(i)
        ERC20(_coin).approve(_pool, MAX_UINT256)
        self.pool_data[_pool].coins[i] = _coin
        _length = self.markets[_coin].length
        self.markets[_coin].addresses[_length] = _pool
        self.markets[_coin].length = _length + 1

        # add underlying coin
        _ucoin: address = CurvePool(_pool).underlying_coins(i)
        if _ucoin != _coin:
            ERC20(_ucoin).approve(_pool, MAX_UINT256)

        self.pool_data[_pool].underlying_coins[i] = _ucoin
        _length = self.underlying_markets[_ucoin].length
        self.underlying_markets[_ucoin].addresses[_length] = _pool
        self.underlying_markets[_ucoin].length = _length + 1

    return True


@public
def remove_pool(_pool: address) -> bool:
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] != ZERO_ADDRESS  # dev: pool does not exist

    # remove _pool from pool_list
    _location: int128 = self.pool_data[_pool].location
    _length: int128 = self.pool_count - 1

    if _location < _length:
        # replace _pool with final value in pool_list
        _addr: address = self.pool_list[_length]
        self.pool_list[_location] = _addr
        self.pool_data[_addr].location = _location

    # delete final pool_list value
    self.pool_list[_length] = ZERO_ADDRESS
    self.pool_count = _length

    for i in range(MAX_COINS):
        _coin: address = self.pool_data[_pool].coins[i]
        if _coin == ZERO_ADDRESS:
            break

        # delete coin address from pool_data
        self.pool_data[_pool].coins[i] = ZERO_ADDRESS

        # remove coin from markets
        _length = self.markets[_coin].length - 1
        for x in range(65536):
            if x > _length:
                break
            if self.markets[_coin].addresses[x] == _pool:
                self.markets[_coin].addresses[x] = self.markets[_coin].addresses[_length]
                break
        self.markets[_coin].addresses[_length] = ZERO_ADDRESS
        self.markets[_coin].length = _length

        # delete underlying_coin from pool_data
        _coin = self.pool_data[_pool].underlying_coins[i]
        self.pool_data[_pool].underlying_coins[i] = ZERO_ADDRESS

        # remove underlying_coin from underlying_markets
        _length = self.underlying_markets[_coin].length - 1
        for x in range(65536):
            if x > _length:
                break
            if self.underlying_markets[_coin].addresses[x] == _pool:
                self.underlying_markets[_coin].addresses[x] = self.underlying_markets[_coin].addresses[_length]
                break
        self.underlying_markets[_coin].addresses[_length] = ZERO_ADDRESS
        self.underlying_markets[_coin].length = _length

    return True


@public
@constant
def get_pool_info(_pool: address) -> (uint256, uint256, address[MAX_COINS], address[MAX_COINS]):
    return (
        CurvePool(_pool).A(),
        CurvePool(_pool).fee(),
        self.pool_data[_pool].coins,
        self.pool_data[_pool].underlying_coins,
    )


@public
@constant
def find_pool_for_coins(_buying: address, _selling: address, i: uint256) -> address:
    _increment: uint256 = i

    _length: int128 = self.markets[_buying].length
    for x in range(65536):
        if x == _length:
            break
        _pool: address = self.markets[_buying].addresses[x]
        if _selling in self.pool_data[_pool].coins:
            if _increment == 0:
                return _pool
            _increment -= 1

    _length = self.underlying_markets[_buying].length
    for x in range(65536):
        if x == _length:
            break
        _pool: address = self.underlying_markets[_buying].addresses[x]
        if _selling in self.pool_data[_pool].underlying_coins:
            if _increment == 0:
                return _pool
            _increment -= 1

    return ZERO_ADDRESS


@public
@constant
def get_pool_balances(_pool: address) -> (uint256[MAX_COINS], uint256[MAX_COINS]):
    _balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    _underlying_balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])

    for i in range(7):
        _coin: address = self.pool_data[_pool].coins[i]
        if _coin == ZERO_ADDRESS:
            break
        _balances[i] = ERC20(_coin).balanceOf(_pool)
        _underlying_coin: address = self.pool_data[_pool].underlying_coins[i]
        if _coin == _underlying_coin:
            _underlying_balances[i] = _balances[i]
        else:
            _underlying_balances[i] = ERC20(_underlying_coin).balanceOf(_pool)

    return _balances, _underlying_balances


@private
@constant
def _get_token_indices(_pool: address, _buying: address, _selling: address) -> (int128, int128):
    i: int128 = -1
    j: int128 = -1

    for x in range(7):
        _coin: address = self.pool_data[_pool].coins[x]
        if _coin == _buying:
            i = x
        elif _coin == _selling:
            j = x
        elif _coin == ZERO_ADDRESS:
            break
    assert min(i, j) != -1

    return i, j


@public
@constant
def get_dy(_pool: address, _buying: address, _selling: address, dx: uint256) -> uint256:
    i: int128 = 0
    j: int128 = 0
    i, j = self._get_token_indices(_pool, _buying, _selling)

    return CurvePool(_pool).get_dy(i, j, dx)


@public
@nonreentrant('lock')
def exchange(_pool: address, _buying: address, _selling: address, dx: uint256, min_dy: uint256):
    i: int128 = 0
    j: int128 = 0
    i, j = self._get_token_indices(_pool, _buying, _selling)

    _initial_balance: uint256 = ERC20(_selling).balanceOf(self)
    ERC20(_buying).transferFrom(msg.sender, self, dx)
    CurvePool(_pool).exchange(i, j, dx, min_dy)
    dy: uint256 = ERC20(_selling).balanceOf(self) - _initial_balance
    ERC20(_selling).transfer(msg.sender, dy)
