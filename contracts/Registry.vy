# @version 0.1.0

from vyper.interfaces import ERC20

MAX_COINS: constant(int128) = 7

struct AddressArray:
    length: int128
    addresses: address[65536]

struct PoolArray:
    location: int128
    decimals: bytes32
    coins: address[MAX_COINS]
    ul_coins: address[MAX_COINS]
    calldata: bytes[72]

struct PoolCoins:
    coins: address[MAX_COINS]
    underlying_coins: address[MAX_COINS]
    decimals: uint256[MAX_COINS]

struct PoolInfo:
    balances: uint256[MAX_COINS]
    underlying_balances: uint256[MAX_COINS]
    decimals: uint256[MAX_COINS]
    A: uint256
    fee: uint256

contract CurvePool:
    def A() -> uint256: constant
    def fee() -> uint256: constant
    def coins(i: int128) -> address: constant
    def underlying_coins(i: int128) -> address: constant
    def get_dy(i: int128, j: int128, dx: uint256) -> uint256: constant
    def get_dy_underlying(i: int128, j: int128, dx: uint256) -> uint256: constant
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): modifying
    def exchange_underlying(i: int128, j: int128, dx: uint256, min_dy: uint256): modifying


admin: address
transfer_ownership_deadline: uint256
future_admin: address

pool_list: public(address[65536])  # master list of pools
pool_count: public(int128)         # actual length of pool_list

pool_data: map(address, PoolArray)      # data for specific pools
markets: map(address, AddressArray)     # list of pools where coin is tradeable
ul_markets: map(address, AddressArray)  # list of pools where underlying coin is tradeable


@public
def __init__():
    self.admin = msg.sender


@public
def add_pool(
    _pool: address,
    _n_coins: int128,
    _decimals: uint256[MAX_COINS],
    _calldata: bytes[72],
):
    """
    @notice Add a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to add
    @param _n_coins Number of coins in the pool
    @param _decimals Underlying coin decimal values
    @param _calldata Calldata to query coin rates
    """

    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    # add pool to pool_list
    _length: int128 = self.pool_count
    self.pool_list[_length] = _pool
    self.pool_count = _length + 1
    self.pool_data[_pool].location = _length
    self.pool_data[_pool].calldata = _calldata

    _decimals_packed: uint256 = 0

    for i in range(MAX_COINS):
        if i == _n_coins:
            break

        _decimals_packed += shift(_decimals[i], i * 16)

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

        self.pool_data[_pool].ul_coins[i] = _ucoin
        _length = self.ul_markets[_ucoin].length
        self.ul_markets[_ucoin].addresses[_length] = _pool
        self.ul_markets[_ucoin].length = _length + 1

    self.pool_data[_pool].decimals = convert(_decimals_packed, bytes32)


@public
def remove_pool(_pool: address):
    """
    @notice Remove a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to remove
    """
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
        _coin = self.pool_data[_pool].ul_coins[i]
        self.pool_data[_pool].ul_coins[i] = ZERO_ADDRESS

        # remove underlying_coin from ul_markets
        _length = self.ul_markets[_coin].length - 1
        for x in range(65536):
            if x > _length:
                break
            if self.ul_markets[_coin].addresses[x] == _pool:
                self.ul_markets[_coin].addresses[x] = self.ul_markets[_coin].addresses[_length]
                break
        self.ul_markets[_coin].addresses[_length] = ZERO_ADDRESS
        self.ul_markets[_coin].length = _length


@public
@constant
def get_pool_coins(_pool: address) -> PoolCoins:
    """
    @notice Get information on coins in a pool
    @dev Empty values in the returned arrays may be ignored
    @param _pool Pool address
    @return Coin addresses, underlying coin addresses, underlying coin decimals
    """
    _coins: PoolCoins = empty(PoolCoins)
    _decimals_packed: bytes32 = self.pool_data[_pool].decimals

    for i in range(MAX_COINS):
        _coins.coins[i] = self.pool_data[_pool].coins[i]
        if _coins.coins[i] == ZERO_ADDRESS:
            break
        _coins.decimals[i] = convert(slice(_decimals_packed, 30 - (i * 2), 2), uint256)
        _coins.underlying_coins[i] = self.pool_data[_pool].ul_coins[i]

    return _coins


@public
@constant
def get_pool_info(_pool: address) -> PoolInfo:
    """
    @notice Get information on a pool
    @dev Reverts if the pool address is unknown
    @param _pool Pool address
    @return balances, underlying balances, underlying decimals, amplification coefficient, fees
    """
    _pool_info: PoolInfo = PoolInfo({
        balances: empty(uint256[MAX_COINS]),
        underlying_balances: empty(uint256[MAX_COINS]),
        decimals: empty(uint256[MAX_COINS]),
        A: CurvePool(_pool).A(),
        fee: CurvePool(_pool).fee()
    })

    _decimals_packed: bytes32 = self.pool_data[_pool].decimals

    for i in range(MAX_COINS):
        _coin: address = self.pool_data[_pool].coins[i]
        if _coin == ZERO_ADDRESS:
            assert i != 0
            break
        _pool_info.decimals[i] = convert(slice(_decimals_packed, 30 - (i * 2), 2), uint256)
        _pool_info.balances[i] = ERC20(_coin).balanceOf(_pool)
        _underlying_coin: address = self.pool_data[_pool].ul_coins[i]
        if _coin == _underlying_coin:
            _pool_info.underlying_balances[i] = _pool_info.balances[i]
        else:
            _pool_info.underlying_balances[i] = ERC20(_underlying_coin).balanceOf(_pool)

    return _pool_info


@public
@constant
def get_pool_rates(_pool: address) -> uint256[MAX_COINS]:
    """
    @notice Get rates between coins and underlying coins
    @dev For coins where there is no underlying coin, or where
         the underlying coin cannot be swapped, the rate is
         given as 1e18
    @param _pool Pool address
    @return Rates between coins and underlying coins
    """
    _rates: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    _calldata: bytes[72] = self.pool_data[_pool].calldata
    for i in range(MAX_COINS):
        _coin: address = self.pool_data[_pool].coins[i]
        if _coin == ZERO_ADDRESS:
            break
        if _coin == self.pool_data[_pool].ul_coins[i]:
            _rates[i] = 10 ** 18
        else:
            _response: bytes[32] = raw_call(_coin, _calldata, max_outsize=32, is_static_call=True)  # dev: bad response
            _rates[i] = convert(_response, uint256)

    return _rates


@public
@constant
def find_pool_for_coins(_from: address, _to: address, i: uint256 = 0) -> address:
    """
    @notice Find an available pool for exchanging two coins
    @dev For coins where there is no underlying coin, or where
         the underlying coin cannot be swapped, the rate is
         given as 1e18
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param i Index value. When multiple pools are available
            this value is used to return the n'th address.
    @return Pool address
    """
    _increment: uint256 = i

    _length: int128 = self.markets[_from].length
    for x in range(65536):
        if x == _length:
            break
        _pool: address = self.markets[_from].addresses[x]
        if _to in self.pool_data[_pool].coins:
            if _increment == 0:
                return _pool
            _increment -= 1

    _length = self.ul_markets[_from].length
    for x in range(65536):
        if x == _length:
            break
        _pool: address = self.ul_markets[_from].addresses[x]
        if _to in self.pool_data[_pool].ul_coins:
            if _increment == 0:
                return _pool
            _increment -= 1

    return ZERO_ADDRESS


@private
@constant
def _get_token_indices(
    _pool: address,
    _from: address,
    _to: address
) -> (int128, int128, bool):
    """
    Convert coin addresses to indices for use with pool methods.
    """
    i: int128 = -1
    j: int128 = -1
    _coin: address = ZERO_ADDRESS
    _check_underlying: bool = True

    # check coin markets
    for x in range(MAX_COINS):
        _coin = self.pool_data[_pool].coins[x]
        if _coin == _from:
            i = x
        elif _coin == _to:
            j = x
        elif _coin == ZERO_ADDRESS:
            break
        else:
            continue
        if min(i, j) > -1:
            return i, j, False
        if _coin != self.pool_data[_pool].ul_coins[x]:
            _check_underlying = False

    assert _check_underlying, "No available market"

    # check underlying coin markets
    for x in range(MAX_COINS):
        _coin = self.pool_data[_pool].ul_coins[x]
        if _coin == _from:
            i = x
        elif _coin == _to:
            j = x
        elif _coin == ZERO_ADDRESS:
            break
        else:
            continue
        if i > -1 and j > -1:
            return i, j, True

    raise "No available market"


@public
@constant
def get_exchange_amount(
    _pool: address,
    _from: address,
    _to: address,
    _amount: uint256
) -> uint256:
    """
    @notice Get the current number of coins received in an exchange
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param _amount Quantity of `_from` to be sent
    @return Quantity of `_to` to be received
    """
    i: int128 = 0
    j: int128 = 0
    _is_underlying: bool = False
    i, j, _is_underlying = self._get_token_indices(_pool, _from, _to)

    if _is_underlying:
        return CurvePool(_pool).get_dy_underlying(i, j, _amount)
    else:
        return CurvePool(_pool).get_dy(i, j, _amount)


@public
@nonreentrant("lock")
def exchange(
    _pool: address,
    _from: address,
    _to: address,
    _amount: uint256,
    _expected: uint256
) -> bool:
    """
    @notice Perform an exchange.
    @dev Prior to calling this function you must approve
         this contract to transfer `_amount` coins from `_from`
    @param _from Address of coin being sent
    @param _to Address of coin being received
    @param _amount Quantity of `_from` being sent
    @param _expected Minimum quantity of `_from` received
           in order for the transaction to succeed
    @return True
    """
    i: int128 = 0
    j: int128 = 0
    _is_underlying: bool = False
    i, j, _is_underlying = self._get_token_indices(_pool, _from, _to)

    _initial_balance: uint256 = ERC20(_to).balanceOf(self)

    _response: bytes[32] = raw_call(
        _from,
        concat(
            method_id("transferFrom(address,address,uint256)", bytes[4]),
            convert(msg.sender, bytes32),
            convert(self, bytes32),
            convert(_amount, bytes32)
        ),
        max_outsize=32
    )
    if len(_response) != 0:
        assert convert(_response, bool)

    if _is_underlying:
        CurvePool(_pool).exchange_underlying(i, j, _amount, _expected)
    else:
        CurvePool(_pool).exchange(i, j, _amount, _expected)

    _received: uint256 = ERC20(_to).balanceOf(self) - _initial_balance
    _response = raw_call(
        _to,
        concat(
            method_id("transfer(address,uint256)", bytes[4]),
            convert(msg.sender, bytes32),
            convert(_received, bytes32)
        ),
        max_outsize=32
    )
    if len(_response) != 0:
        assert convert(_response, bool)

    return True


# Admin functions

@public
def commit_transfer_ownership(_new_admin: address):
    """
    @notice Initiate a transfer of contract ownership
    @dev Once initiated, the actual transfer may be performed three days later
    @param _new_admin Address of the new owner account
    """
    assert msg.sender == self.admin
    assert self.transfer_ownership_deadline == 0

    self.transfer_ownership_deadline = block.timestamp + 3*86400
    self.future_admin = _new_admin


@public
def apply_transfer_ownership():
    """
    @notice Finalize a transfer of contract ownership
    @dev May only be called by the current owner, three days after a
         call to `commit_transfer_ownership`
    """
    assert msg.sender == self.admin
    assert self.transfer_ownership_deadline != 0
    assert block.timestamp >= self.transfer_ownership_deadline

    self.admin = self.future_admin
    self.transfer_ownership_deadline = 0


@public
def revert_transfer_ownership():
    """
    @notice Revert a transfer of contract ownership
    @dev May only be called by the current owner
    """
    assert msg.sender == self.admin

    self.transfer_ownership_deadline = 0
