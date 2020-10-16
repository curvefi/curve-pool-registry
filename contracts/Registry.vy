# @version 0.2.7

MAX_COINS: constant(int128) = 8
CALC_INPUT_SIZE: constant(int128) = 100


struct PoolArray:
    location: uint256
    decimals: uint256
    underlying_decimals: uint256
    rate_method_id: bytes32
    lp_token: address
    base_pool: address
    coins: address[MAX_COINS]
    ul_coins: address[MAX_COINS]
    n_coins: uint256
    has_initial_A: bool
    is_v1: bool

struct PoolInfo:
    balances: uint256[MAX_COINS]
    underlying_balances: uint256[MAX_COINS]
    decimals: uint256[MAX_COINS]
    underlying_decimals: uint256[MAX_COINS]
    rates: uint256[MAX_COINS]
    lp_token: address
    A: uint256
    future_A: uint256
    fee: uint256
    future_fee: uint256
    future_admin_fee: uint256
    future_owner: address
    initial_A: uint256
    initial_A_time: uint256
    future_A_time: uint256

struct PoolCoins:
    coins: address[MAX_COINS]
    underlying_coins: address[MAX_COINS]
    decimals: uint256[MAX_COINS]
    underlying_decimals: uint256[MAX_COINS]

struct PoolGauges:
    liquidity_gauges: address[10]
    gauge_types: int128[10]


interface ERC20:
    def balanceOf(_addr: address) -> uint256: view
    def decimals() -> uint256: view

interface CurvePool:
    def A() -> uint256: view
    def future_A() -> uint256: view
    def fee() -> uint256: view
    def admin_fee() -> uint256: view
    def future_fee() -> uint256: view
    def future_admin_fee() -> uint256: view
    def future_owner() -> address: view
    def initial_A() -> uint256: view
    def initial_A_time() -> uint256: view
    def future_A_time() -> uint256: view
    def coins(i: uint256) -> address: view
    def underlying_coins(i: uint256) -> address: view
    def balances(i: uint256) -> uint256: view
    def get_virtual_price() -> uint256: view

interface CurvePoolV1:
    def coins(i: int128) -> address: view
    def underlying_coins(i: int128) -> address: view
    def balances(i: int128) -> uint256: view

interface CurveMetapool:
    def base_pool() -> address: view

interface GasEstimator:
    def estimate_gas_used(_pool: address, _from: address, _to: address) -> uint256: view

interface LiquidityGauge:
    def lp_token() -> address: view

interface GaugeController:
    def gauge_types(gauge: address) -> int128: view


event CommitNewAdmin:
    deadline: indexed(uint256)
    admin: indexed(address)

event NewAdmin:
    admin: indexed(address)

event PoolAdded:
    pool: indexed(address)
    rate_method_id: Bytes[4]

event PoolRemoved:
    pool: indexed(address)


admin: public(address)
transfer_ownership_deadline: uint256
future_admin: address

gauge_controller: address
pool_list: public(address[65536])   # master list of pools
pool_count: public(uint256)         # actual length of pool_list

pool_data: HashMap[address, PoolArray]

# lp token -> pool
get_pool_from_lp_token: public(HashMap[address, address])

# mapping of estimated gas costs for pools and coins
# for a pool the values are [wrapped exchange, underlying exchange]
# for a coin the values are [transfer cost, 0]
gas_estimate_values: HashMap[address, uint256[2]]

# pool -> gas estimation contract
# used when gas costs for a pool are too complex to be handled by summing
# values in `gas_estimate_values`
gas_estimate_contracts: HashMap[address, address]

# mapping of coin -> coin -> pools for trading
# all addresses are converted to uint256 prior to storage. coin addresses are stored
# using the smaller value first. within each pool address array, the first value
# is shifted 16 bits to the left, and these 16 bits are used to store the array length.

markets: HashMap[uint256, address[65536]]
market_counts: HashMap[uint256, uint256]

liquidity_gauges: HashMap[address, address[10]]


@external
def __init__(_gauge_controller: address):
    """
    @notice Constructor function
    """
    self.admin = msg.sender
    self.gauge_controller = _gauge_controller


@view
@external
def find_pool_for_coins(_from: address, _to: address, i: uint256 = 0) -> address:
    """
    @notice Find an available pool for exchanging two coins
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param i Index value. When multiple pools are available
            this value is used to return the n'th address.
    @return Pool address
    """

    key: uint256 = bitwise_xor(convert(_from, uint256), convert(_to, uint256))
    return self.markets[key][i]


@view
@external
def get_n_coins(_pool: address) -> uint256[2]:
    n_coins: uint256 = self.pool_data[_pool].n_coins
    return [shift(n_coins, -128), n_coins % 2**128]


@view
@internal
def _get_rates(_pool: address) -> uint256[MAX_COINS]:
    rates: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    base_pool: address = self.pool_data[_pool].base_pool
    if base_pool == ZERO_ADDRESS:
        rate_method_id: Bytes[4] = slice(self.pool_data[_pool].rate_method_id, 0, 4)

        for i in range(MAX_COINS):
            coin: address = self.pool_data[_pool].coins[i]
            if coin == ZERO_ADDRESS:
                break
            if coin == self.pool_data[_pool].ul_coins[i]:
                rates[i] = 10 ** 18
            else:
                rates[i] = convert(
                    raw_call(coin, rate_method_id, max_outsize=32, is_static_call=True), # dev: bad response
                    uint256
                )
    else:
        base_coin_idx: uint256 = shift(self.pool_data[_pool].n_coins, -128) - 1
        rates[base_coin_idx] = CurvePool(base_pool).get_virtual_price()
        for i in range(MAX_COINS):
            if i == base_coin_idx:
                break
            rates[i] = 10 ** 18


    return rates


@view
@external
def get_rates(_pool: address) -> uint256[MAX_COINS]:
    """
    @notice Get rates between coins and underlying coins
    @dev For coins where there is no underlying coin, or where
         the underlying coin cannot be swapped, the rate is
         given as 1e18
    @param _pool Pool address
    @return Rates between coins and underlying coins
    """
    return self._get_rates(_pool)


@view
@external
def get_lp_token(_pool: address) -> address:
    """
    @notice Get the address of the LP token for a pool
    @param _pool Pool address
    @return LP token address
    """
    return self.pool_data[_pool].lp_token


@view
@external
def get_gauges(_pool: address) -> PoolGauges:
    """
    @notice Get a list of LiquidityGauge contracts associated with a pool
    @param _pool Pool address
    @return address[10] of gauge addresses, int128[10] of gauge types
    """
    gauge_info: PoolGauges = empty(PoolGauges)
    gauge_controller: address = self.gauge_controller
    for i in range(10):
        gauge: address = self.liquidity_gauges[_pool][i]
        if gauge == ZERO_ADDRESS:
            break
        gauge_info.liquidity_gauges[i] = gauge
        gauge_info.gauge_types[i] = GaugeController(gauge_controller).gauge_types(gauge)

    return gauge_info


@view
@internal
def _get_balances(_pool: address) -> uint256[MAX_COINS]:
    is_v1: bool = self.pool_data[_pool].is_v1

    balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        coin: address = self.pool_data[_pool].coins[i]
        if coin == ZERO_ADDRESS:
            assert i != 0
            break

        if is_v1:
            balances[i] = CurvePoolV1(_pool).balances(i)
        else:
            balances[i] = CurvePool(_pool).balances(convert(i, uint256))

    return balances


@view
@internal
def _get_underlying_balances(
    _pool: address,
    _balances: uint256[MAX_COINS],
    _rates: uint256[MAX_COINS]
) -> uint256[MAX_COINS]:
    underlying_balances: uint256[MAX_COINS] = _balances
    for i in range(MAX_COINS):
        coin: address = self.pool_data[_pool].coins[i]
        if coin == ZERO_ADDRESS:
            break
        ucoin: address = self.pool_data[_pool].ul_coins[i]
        if ucoin == ZERO_ADDRESS:
            continue
        if ucoin != coin:
            underlying_balances[i] = _balances[i] * _rates[i] / 10 ** 18

    return underlying_balances


@view
@internal
def _get_meta_underlying_balances(_pool: address, _base_pool: address) -> uint256[MAX_COINS]:

    base_coin_idx: uint256 = shift(self.pool_data[_pool].n_coins, -128) - 1
    underlying_balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    for i in range(MAX_COINS):
        ucoin: address = self.pool_data[_pool].ul_coins[i]
        if ucoin == ZERO_ADDRESS:
            break
        if i < base_coin_idx:
            underlying_balances[i] = CurvePool(_pool).balances(i)
        else:
            underlying_balances[i] = CurvePool(_base_pool).balances(i - base_coin_idx)

    return underlying_balances



@view
@external
def get_balances(_pool: address) -> uint256[MAX_COINS]:
    return self._get_balances(_pool)


@view
@external
def get_underlying_balances(_pool: address) -> uint256[MAX_COINS]:
    base_pool: address = self.pool_data[_pool].base_pool
    if base_pool == ZERO_ADDRESS:
        return self._get_underlying_balances(
            _pool,
            self._get_balances(_pool),
            self._get_rates(_pool),
        )
    return self._get_meta_underlying_balances(_pool, base_pool)


@view
@external
def get_coins(_pool: address) -> address[MAX_COINS]:
    coins: address[MAX_COINS] = empty(address[MAX_COINS])
    n_coins: uint256 = shift(self.pool_data[_pool].n_coins, -128)
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        coins[i] = self.pool_data[_pool].coins[i]

    return coins


@view
@external
def get_underlying_coins(_pool: address) -> address[MAX_COINS]:
    coins: address[MAX_COINS] = empty(address[MAX_COINS])
    n_coins: uint256 = self.pool_data[_pool].n_coins % 2**128
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        coins[i] = self.pool_data[_pool].ul_coins[i]

    return coins


@view
@internal
def _unpack_decimals(_packed: uint256, _n_coins: uint256) -> uint256[MAX_COINS]:
    decimals: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    n_coins: int128 = convert(_n_coins, int128)
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        decimals[i] = shift(_packed, -8 * i) % 256

    return decimals


@view
@external
def get_decimals(_pool: address) -> uint256[MAX_COINS]:
    n_coins: uint256 = shift(self.pool_data[_pool].n_coins, -128)
    return self._unpack_decimals(self.pool_data[_pool].decimals, n_coins)


@view
@external
def get_underlying_decimals(_pool: address) -> uint256[MAX_COINS]:
    n_coins: uint256 = self.pool_data[_pool].n_coins % 2**128
    return self._unpack_decimals(self.pool_data[_pool].underlying_decimals, n_coins)


@view
@external
def get_A(_pool: address) -> uint256:
    return CurvePool(_pool).A()


@view
@external
def get_fees(_pool: address) -> (uint256, uint256):
    return CurvePool(_pool).fee(), CurvePool(_pool).admin_fee()


@view
@external
def get_admin_balances(_pool: address) -> uint256[MAX_COINS]:
    balances: uint256[MAX_COINS] = self._get_balances(_pool)
    n_coins: uint256 = shift(self.pool_data[_pool].n_coins, -128)
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        balances[i] -= ERC20(self.pool_data[_pool].coins[i]).balanceOf(_pool)

    return balances


@view
@internal
def _get_coin_indices(
    _pool: address,
    _from: address,
    _to: address
) -> (int128, int128, bool):
    """
    Convert coin addresses to indices for use with pool methods.
    """
    i: int128 = -1
    j: int128 = i
    check_underlying: bool = True

    # check coin markets
    for x in range(MAX_COINS):
        coin: address = self.pool_data[_pool].coins[x]
        if coin == _from:
            i = x
        elif coin == _to:
            j = x
        elif coin == ZERO_ADDRESS:
            break
        else:
            continue
        if i >= 0 and j >= 0:
            return i, j, False
        if coin != self.pool_data[_pool].ul_coins[x]:
            check_underlying = False

    if check_underlying:
        # check underlying coin markets
        for x in range(MAX_COINS):
            coin: address = self.pool_data[_pool].ul_coins[x]
            if coin == _from:
                i = x
            elif coin == _to:
                j = x
            elif coin == ZERO_ADDRESS:
                break
            else:
                continue
            if i >= 0 and j >= 0:
                return i, j, True

    raise "No available market"


@view
@external
def get_coin_indices(
    _pool: address,
    _from: address,
    _to: address
) -> (int128, int128, bool):
    """
    Convert coin addresses to indices for use with pool methods.
    """
    return self._get_coin_indices(_pool, _from, _to)


@view
@external
def estimate_gas_used(_pool: address, _from: address, _to: address) -> uint256:
    """
    @notice Estimate the gas used in an exchange.
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @return Upper-bound gas estimate, in wei
    """
    estimator: address = self.gas_estimate_contracts[_pool]
    if estimator != ZERO_ADDRESS:
        return GasEstimator(estimator).estimate_gas_used(_pool, _from, _to)

    # here we call `_get_coin_indices` to find out if the exchange involves
    # wrapped or underlying coins, and convert the result to an integer that we
    # use as an index for `gas_estimate_values`
    # 0 == wrapped   1 == underlying
    idx_underlying: uint256 = convert(self._get_coin_indices(_pool, _from, _to)[2], uint256)

    total: uint256 = self.gas_estimate_values[_pool][idx_underlying]
    assert total != 0  # dev: pool value not set

    for addr in [_from, _to]:
        _gas: uint256 = self.gas_estimate_values[addr][0]
        assert _gas != 0  # dev: coin value not set
        total += _gas

    return total


# large view methods - not optimized, intended for off-chain calls

@view
@external
def get_pool_coins(_pool: address) -> PoolCoins:
    """
    @notice Get information on coins in a pool
    @dev Empty values in the returned arrays may be ignored
    @param _pool Pool address
    @return Coin addresses, underlying coin addresses, underlying coin decimals
    """
    coins: PoolCoins = empty(PoolCoins)
    decimals_packed: uint256 = self.pool_data[_pool].decimals

    n_coins_packed: uint256 = self.pool_data[_pool].n_coins
    n_coins: int128 = convert(shift(n_coins_packed, -128), int128)
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        coins.coins[i] = self.pool_data[_pool].coins[i]
        coins.decimals[i] = shift(decimals_packed, -8 * i) % 256

    n_coins = convert(n_coins_packed % 2**128, int128)
    decimals_packed = self.pool_data[_pool].underlying_decimals
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        coins.underlying_coins[i] = self.pool_data[_pool].ul_coins[i]
        if coins.underlying_coins[i] != ZERO_ADDRESS:
            coins.underlying_decimals[i] = shift(decimals_packed, -8 * i) % 256

    return coins


@view
@external
def get_pool_info(_pool: address) -> PoolInfo:
    """
    @notice Get information on a pool
    @dev Reverts if the pool address is unknown
    @param _pool Pool address
    @return balances, underlying balances, decimals, underlying decimals,
            lp token, amplification coefficient, fees
    """
    pool_info: PoolInfo = empty(PoolInfo)

    pool_info.rates = self._get_rates(_pool)
    pool_info.balances = self._get_balances(_pool)

    base_pool: address = self.pool_data[_pool].base_pool
    if base_pool == ZERO_ADDRESS:
        pool_info.underlying_balances = self._get_underlying_balances(_pool, pool_info.balances, pool_info.rates)
    else:
        pool_info.underlying_balances = self._get_meta_underlying_balances(_pool, base_pool)

    n_coins_packed: uint256 = self.pool_data[_pool].n_coins
    pool_info.decimals = self._unpack_decimals(
        self.pool_data[_pool].decimals,
        shift(n_coins_packed, -128)
    )
    pool_info.underlying_decimals = self._unpack_decimals(
        self.pool_data[_pool].underlying_decimals,
        n_coins_packed % 2**128
    )

    pool_info.lp_token = self.pool_data[_pool].lp_token

    pool_info.A = CurvePool(_pool).A()
    pool_info.future_A = CurvePool(_pool).future_A()
    pool_info.fee = CurvePool(_pool).fee()
    pool_info.future_fee = CurvePool(_pool).future_fee()
    pool_info.future_admin_fee = CurvePool(_pool).future_admin_fee()
    pool_info.future_owner = CurvePool(_pool).future_owner()

    if self.pool_data[_pool].has_initial_A:
        pool_info.initial_A = CurvePool(_pool).initial_A()
        pool_info.initial_A_time = CurvePool(_pool).initial_A_time()
        pool_info.future_A_time = CurvePool(_pool).future_A_time()

    return pool_info


# Admin functions


@view
@internal
def _get_decimals(_coins: address[MAX_COINS], _n_coins: uint256) -> uint256:
    packed: uint256 = 0
    value: uint256 = 0

    n_coins: int128 = convert(_n_coins, int128)
    for i in range(MAX_COINS):
        if i == n_coins:
            break
        coin: address = _coins[i]
        if coin == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
            value = 18
        else:
            value = ERC20(coin).decimals()
            assert value < 256  # dev: decimal overflow

        packed += shift(value, i * 8)

    return packed


@internal
def _add_pool(
    _pool: address,
    _n_coins: uint256,
    _lp_token: address,
    _rate_method_id: bytes32,
    _has_initial_A: bool,
    _is_v1: bool,
):
    # add pool to pool_list
    length: uint256 = self.pool_count
    self.pool_list[length] = _pool
    self.pool_count = length + 1
    self.pool_data[_pool].location = length
    self.pool_data[_pool].lp_token = _lp_token
    self.pool_data[_pool].rate_method_id = _rate_method_id
    self.pool_data[_pool].has_initial_A = _has_initial_A
    self.pool_data[_pool].is_v1 = _is_v1
    self.pool_data[_pool].n_coins = _n_coins

    # update public mappings
    self.get_pool_from_lp_token[_lp_token] = _pool

    log PoolAdded(_pool, slice(_rate_method_id, 0, 4))


@internal
def _get_new_pool_coins(
    _pool: address,
    _n_coins: uint256,
    _is_underlying: bool,
    _is_v1: bool
) -> address[MAX_COINS]:
    coin_list: address[MAX_COINS] = empty(address[MAX_COINS])
    coin: address = ZERO_ADDRESS
    for i in range(MAX_COINS):
        if i == _n_coins:
            break
        if _is_underlying:
            if _is_v1:
                coin = CurvePoolV1(_pool).underlying_coins(convert(i, int128))
            else:
                coin = CurvePool(_pool).underlying_coins(i)
            self.pool_data[_pool].ul_coins[i] = coin
        else:
            if _is_v1:
                coin = CurvePoolV1(_pool).coins(convert(i, int128))
            else:
                coin = CurvePool(_pool).coins(i)
            self.pool_data[_pool].coins[i] = coin
        coin_list[i] = coin

    for i in range(MAX_COINS):
        if i == _n_coins:
            break

        # add pool to markets
        i2: uint256 = i + 1
        for x in range(i2, i2 + MAX_COINS):
            if x == _n_coins:
                break

            key: uint256 = bitwise_xor(convert(coin_list[i], uint256), convert(coin_list[x], uint256))
            length: uint256 = self.market_counts[key]
            self.markets[key][length] = _pool
            self.market_counts[key] = length + 1

    return coin_list


@external
def add_pool(
    _pool: address,
    _n_coins: uint256,
    _lp_token: address,
    _rate_method_id: bytes32,
    _decimals: uint256,
    _underlying_decimals: uint256,
    _has_initial_A: bool,
    _is_v1: bool,
):
    """
    @notice Add a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to add
    @param _n_coins Number of coins in the pool
    @param _lp_token Pool deposit token address
    @param _rate_method_id Encoded four-byte function signature to query
                           coin rates, right padded to bytes32
    @param _decimals Coin decimal values, tightly packed as uint8 and right
                     padded as bytes32
    @param _underlying_decimals Underlying coin decimal values, tightly packed
                                as uint8 and right padded as bytes32
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    coins: address[MAX_COINS] = self._get_new_pool_coins(_pool, _n_coins, False, _is_v1)
    decimals: uint256 = _decimals
    if decimals == 0:
        decimals = self._get_decimals(coins, _n_coins)
    self.pool_data[_pool].decimals = decimals
    self.pool_data[_pool].coins = coins

    coins = self._get_new_pool_coins(_pool, _n_coins, True, _is_v1)
    decimals = _underlying_decimals
    if decimals == 0:
        decimals = self._get_decimals(coins, _n_coins)
    self.pool_data[_pool].underlying_decimals = decimals
    self.pool_data[_pool].ul_coins = coins

    self._add_pool(
        _pool,
        _n_coins + shift(_n_coins, 128),
        _lp_token,
        _rate_method_id,
        _has_initial_A,
        _is_v1,
    )


@external
def add_pool_without_underlying(
    _pool: address,
    _n_coins: uint256,
    _lp_token: address,
    _rate_method_id: bytes32,
    _decimals: uint256,
    _use_rates: uint256,
    _has_initial_A: bool,
    _is_v1: bool,
):
    """
    @notice Add a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to add
    @param _n_coins Number of coins in the pool
    @param _lp_token Pool deposit token address
    @param _rate_method_id Encoded four-byte function signature to query
                           coin rates, right padded as bytes32
    @param _decimals Coin decimal values, tightly packed as uint8 and right
                     padded as bytes32
    @param _use_rates Boolean array indicating which coins use lending rates,
                      tightly packed and right padded as bytes32
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    coins: address[MAX_COINS] = self._get_new_pool_coins(_pool, _n_coins, False, _is_v1)

    decimals: uint256 = _decimals
    if decimals == 0:
        decimals = self._get_decimals(coins, _n_coins)

    self.pool_data[_pool].decimals = decimals
    self.pool_data[_pool].coins = coins

    udecimals: uint256 = 0
    for i in range(MAX_COINS):
        if i == _n_coins:
            break
        offset: int128 = -8 * convert(i, int128)
        if shift(_use_rates, offset) % 256 == 0:
            self.pool_data[_pool].ul_coins[i] = coins[i]
            udecimals += shift(shift(decimals, offset) % 256, -offset)

    self.pool_data[_pool].underlying_decimals = udecimals

    self._add_pool(
        _pool,
        _n_coins + shift(_n_coins, 128),
        _lp_token,
        _rate_method_id,
        _has_initial_A,
        _is_v1,
    )


@external
def add_metapool(
    _pool: address,
    _n_coins: uint256,
    _base_n_coins: uint256,
    _lp_token: address,
    _decimals: uint256,
):
    """
    @notice Add a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to add
    @param _n_coins Number of coins in the pool
    @param _lp_token Pool deposit token address
    @param _decimals Coin decimal values, tightly packed as uint8 and right
                     padded as bytes32
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] == ZERO_ADDRESS  # dev: pool exists

    coins: address[MAX_COINS] = self._get_new_pool_coins(_pool, _n_coins, False, False)

    decimals: uint256 = _decimals
    if decimals == 0:
        decimals = self._get_decimals(coins, _n_coins)
    self.pool_data[_pool].decimals = decimals
    self.pool_data[_pool].coins = coins

    base_pool: address = CurveMetapool(_pool).base_pool()
    assert self.pool_data[base_pool].coins[0] != ZERO_ADDRESS  # dev: base pool unknown
    self.pool_data[_pool].base_pool = base_pool

    base_coin_offset: uint256 = _n_coins - 1
    coin: address = ZERO_ADDRESS
    for i in range(MAX_COINS):
        if i < base_coin_offset:
            coin = coins[i]
        else:
            coin = self.pool_data[base_pool].coins[i - base_coin_offset]
        self.pool_data[_pool].ul_coins[i] = coin

    underlying_decimals: uint256 = shift(
        self.pool_data[base_pool].decimals, 8 * convert(base_coin_offset, int128)
    )
    underlying_decimals += decimals % 256 ** base_coin_offset

    self.pool_data[_pool].underlying_decimals = underlying_decimals

    # TODO metapool underlying - only add some markets!!
    # for i in range(MAX_COINS):
    #     if i == _n_coins:
    #         break

    #     coin = coin_list[i]

    #     # add pool to markets
    #     i2: uint256 = i + 1
    #     for x in range(i2, i2 + MAX_COINS):
    #         if x == _n_coins:
    #             break

    #         coinx: address = coin_list[x]
    #         first: uint256 = min(convert(coin, uint256), convert(coinx, uint256))
    #         second: uint256 = max(convert(coin, uint256), convert(coinx, uint256))

    #         pool_zero: uint256 = self.markets[first][second][0]
    #         length: uint256 = pool_zero % 65536
    #         shifted: uint256 = shift(convert(_pool, uint256), 16) + 1
    #         if pool_zero != 0:
    #             self.markets[first][second][length] = convert(_pool, uint256)
    #             self.markets[first][second][0] = pool_zero + 1
    #         else:
    #             self.markets[first][second][0] = shifted

    self._add_pool(
        _pool,
        _base_n_coins + base_coin_offset + shift(_n_coins, 128),
        _lp_token,
        EMPTY_BYTES32,
        True,
        False,
    )


@internal
def _remove_market(_pool: address, _coina: address, _coinb: address):
    key: uint256 = bitwise_xor(convert(_coina, uint256), convert(_coinb, uint256))
    length: uint256 = self.market_counts[key] - 1
    self.market_counts[key] = length
    for i in range(65536):
        if i > length:
            raise
        if self.markets[key][i] == _pool:
            if i < length:
                self.markets[key][i] = self.markets[key][length]
            self.markets[key][length] = ZERO_ADDRESS
            break



@external
def remove_pool(_pool: address):
    """
    @notice Remove a pool to the registry
    @dev Only callable by admin
    @param _pool Pool address to remove
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.pool_data[_pool].coins[0] != ZERO_ADDRESS  # dev: pool does not exist

    self.get_pool_from_lp_token[self.pool_data[_pool].lp_token] = ZERO_ADDRESS

    # remove _pool from pool_list
    location: uint256 = self.pool_data[_pool].location
    length: uint256 = self.pool_count - 1

    if location < length:
        # replace _pool with final value in pool_list
        addr: address = self.pool_list[length]
        self.pool_list[location] = addr
        self.pool_data[addr].location = location

    # delete final pool_list value
    self.pool_list[length] = ZERO_ADDRESS
    self.pool_count = length

    self.pool_data[_pool].underlying_decimals = 0
    self.pool_data[_pool].decimals = 0

    coins: address[MAX_COINS] = empty(address[MAX_COINS])
    ucoins: address[MAX_COINS] = empty(address[MAX_COINS])

    for i in range(MAX_COINS):
        coins[i] = self.pool_data[_pool].coins[i]
        ucoins[i] = self.pool_data[_pool].ul_coins[i]
        if ucoins[i] == ZERO_ADDRESS and coins[i] == ZERO_ADDRESS:
            break
        if coins[i] != ZERO_ADDRESS:
            # delete coin address from pool_data
            self.pool_data[_pool].coins[i] = ZERO_ADDRESS
        if ucoins[i] != ZERO_ADDRESS:
            # delete underlying_coin from pool_data
            self.pool_data[_pool].ul_coins[i] = ZERO_ADDRESS

    for i in range(MAX_COINS):
        coin: address = coins[i]
        ucoin: address = ucoins[i]
        if coin == ZERO_ADDRESS:
            break

        # remove pool from markets
        i2: uint256 = i + 1
        for x in range(i2, i2 + MAX_COINS):
            ucoinx: address = ucoins[x]
            if ucoinx == ZERO_ADDRESS:
                break

            coinx: address = coins[x]
            if coinx != ZERO_ADDRESS:
                self._remove_market(_pool, coin, coinx)

            if coin != ucoin or coinx != ucoinx:
                self._remove_market(_pool, ucoin, ucoinx)

    log PoolRemoved(_pool)


@external
def set_pool_gas_estimates(_addr: address[5], _amount: uint256[2][5]):
    """
    @notice Set gas estimate amounts
    @param _addr Array of pool addresses
    @param _amount Array of gas estimate amounts as `[(wrapped, underlying), ..]`
    """
    assert msg.sender == self.admin  # dev: admin-only function

    for i in range(5):
        _pool: address = _addr[i]
        if _pool == ZERO_ADDRESS:
            break
        self.gas_estimate_values[_pool] = _amount[i]


@external
def set_coin_gas_estimates(_addr: address[10], _amount: uint256[10]):
    """
    @notice Set gas estimate amounts
    @param _addr Array of coin addresses
    @param _amount Array of gas estimate amounts
    """
    assert msg.sender == self.admin  # dev: admin-only function

    for i in range(10):
        _coin: address = _addr[i]
        if _coin == ZERO_ADDRESS:
            break
        self.gas_estimate_values[_coin][0] = _amount[i]


@external
def set_gas_estimate_contract(_pool: address, _estimator: address):
    """
    @notice Set gas estimate contract
    @param _pool Pool address
    @param _estimator GasEstimator address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.gas_estimate_contracts[_pool] = _estimator


@external
def set_liquidity_gauges(_pool: address, _liquidity_gauges: address[10]):
    """
    @notice Set liquidity gauge contracts``
    @param _pool Pool address
    @param _liquidity_gauges Liquidity gauge address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    _lp_token: address = self.pool_data[_pool].lp_token
    _gauge_controller: address = self.gauge_controller
    for i in range(10):
        _gauge: address = _liquidity_gauges[i]
        if _gauge != ZERO_ADDRESS:
            assert LiquidityGauge(_gauge).lp_token() == _lp_token  # dev: wrong token
            GaugeController(_gauge_controller).gauge_types(_gauge)
            self.liquidity_gauges[_pool][i] = _gauge
        elif self.liquidity_gauges[_pool][i] != ZERO_ADDRESS:
            self.liquidity_gauges[_pool][i] = ZERO_ADDRESS
        else:
            break


@external
def commit_transfer_ownership(_new_admin: address):
    """
    @notice Initiate a transfer of contract ownership
    @dev Once initiated, the actual transfer may be performed three days later
    @param _new_admin Address of the new owner account
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.transfer_ownership_deadline == 0  # dev: transfer already active

    deadline: uint256 = block.timestamp + 3*86400
    self.transfer_ownership_deadline = deadline
    self.future_admin = _new_admin

    log CommitNewAdmin(deadline, _new_admin)


@external
def apply_transfer_ownership():
    """
    @notice Finalize a transfer of contract ownership
    @dev May only be called by the current owner, three days after a
         call to `commit_transfer_ownership`
    """
    assert msg.sender == self.admin  # dev: admin-only function
    assert self.transfer_ownership_deadline != 0  # dev: transfer not active
    assert block.timestamp >= self.transfer_ownership_deadline  # dev: now < deadline

    new_admin: address = self.future_admin
    self.admin = new_admin
    self.transfer_ownership_deadline = 0

    log NewAdmin(new_admin)


@external
def revert_transfer_ownership():
    """
    @notice Revert a transfer of contract ownership
    @dev May only be called by the current owner
    """
    assert msg.sender == self.admin  # dev: admin-only function

    self.transfer_ownership_deadline = 0
