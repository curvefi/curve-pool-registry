# @version 0.2.7

MAX_COINS: constant(int128) = 8
CALC_INPUT_SIZE: constant(uint256) = 100

from vyper.interfaces import ERC20

interface CurvePool:
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): payable
    def exchange_underlying(i: int128, j: int128, dx: uint256, min_dy: uint256): payable
    def get_dy(i: int128, j: int128, amount: uint256) -> uint256: view
    def get_dy_underlying(i: int128, j: int128, amount: uint256) -> uint256: view

interface Registry:
    def get_A(_pool: address) -> uint256: view
    def get_fees(_pool: address) -> (uint256, uint256): view
    def get_coin_indices(_pool: address, _from: address, _to: address) -> (int128, int128, bool): view
    def get_n_coins(_pool: address) -> uint256[2]: view
    def get_balances(_pool: address) -> uint256[MAX_COINS]: view
    def get_underlying_balances(_pool: address) -> uint256[MAX_COINS]: view
    def get_rates(_pool: address) -> uint256[MAX_COINS]: view
    def get_decimals(_pool: address) -> uint256[MAX_COINS]: view
    def get_underlying_decimals(_pool: address) -> uint256[MAX_COINS]: view

interface Calculator:
    def get_dx(n_coins: uint256, balances: uint256[MAX_COINS], amp: uint256, fee: uint256,
               rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS],
               i: int128, j: int128, dx: uint256) -> uint256: view
    def get_dy(n_coins: uint256, balances: uint256[MAX_COINS], amp: uint256, fee: uint256,
               rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS],
               i: int128, j: int128, dx: uint256[CALC_INPUT_SIZE]) -> uint256[CALC_INPUT_SIZE]: view


event TokenExchange:
    buyer: indexed(address)
    pool: indexed(address)
    token_sold: address
    token_bought: address
    amount_sold: uint256
    amount_bought: uint256

event CommitNewAdmin:
    deadline: indexed(uint256)
    admin: indexed(address)

event NewAdmin:
    admin: indexed(address)


admin: public(address)
transfer_ownership_deadline: uint256
future_admin: address

registry: public(address)
default_calculator: public(address)
pool_calculator: HashMap[address, address]

is_approved: HashMap[address, HashMap[address, bool]]


@external
def __init__(_registry: address, _calculator: address):
    """
    @notice Constructor function
    """
    self.admin = msg.sender
    self.registry = _registry
    self.default_calculator = _calculator


@external
@payable
def __default__():
    pass


@view
@external
def get_exchange_amount(_pool: address, _from: address, _to: address, _amount: uint256) -> uint256:
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
    is_underlying: bool = False
    i, j, is_underlying = Registry(self.registry).get_coin_indices(_pool, _from, _to) # dev: no market

    if is_underlying:
        return CurvePool(_pool).get_dy_underlying(i, j, _amount)

    return CurvePool(_pool).get_dy(i, j, _amount)


@view
@external
def get_input_amount(_pool: address, _from: address, _to: address, _amount: uint256) -> uint256:
    """
    @notice Get the current number of coins required to receive the given amount in an exchange
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param _amount Quantity of `_to` to be received
    @return Quantity of `_from` to be sent
    """

    registry: address = self.registry

    i: int128 = 0
    j: int128 = 0
    is_underlying: bool = False
    i, j, is_underlying = Registry(registry).get_coin_indices(_pool, _from, _to)
    amp: uint256 = Registry(registry).get_A(_pool)
    fee: uint256 = Registry(registry).get_fees(_pool)[0]

    balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    rates: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    decimals: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    n_coins: uint256 = Registry(registry).get_n_coins(_pool)[convert(is_underlying, uint256)]
    if is_underlying:
        balances = Registry(registry).get_underlying_balances(_pool)
        decimals = Registry(registry).get_underlying_decimals(_pool)
        for x in range(MAX_COINS):
            if convert(x, uint256) == n_coins:
                break
            rates[x] = 10**18
    else:
        balances = Registry(registry).get_balances(_pool)
        decimals = Registry(registry).get_decimals(_pool)
        rates = Registry(registry).get_rates(_pool)

    for x in range(MAX_COINS):
        if convert(x, uint256) == n_coins:
            break
        decimals[x] = 10 ** (18 - decimals[x])

    calculator: address = self.pool_calculator[_pool]
    if calculator == ZERO_ADDRESS:
        calculator = self.default_calculator
    return Calculator(calculator).get_dx(n_coins, balances, amp, fee, rates, decimals, i, j, _amount)


@view
@external
def get_exchange_amounts(_pool: address, _from: address, _to: address, _amounts: uint256[CALC_INPUT_SIZE]) -> uint256[CALC_INPUT_SIZE]:
    """
    @notice Get the current number of coins required to receive the given amount in an exchange
    @param _pool Pool address
    @param _from Address of coin to be sent
    @param _to Address of coin to be received
    @param _amounts Quantity of `_to` to be received
    @return Quantity of `_from` to be sent
    """

    registry: address = self.registry

    i: int128 = 0
    j: int128 = 0
    is_underlying: bool = False
    balances: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    rates: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
    decimals: uint256[MAX_COINS] = empty(uint256[MAX_COINS])

    amp: uint256 = Registry(registry).get_A(_pool)
    fee: uint256 = Registry(registry).get_fees(_pool)[0]
    i, j, is_underlying = Registry(registry).get_coin_indices(_pool, _from, _to)
    n_coins: uint256 = Registry(registry).get_n_coins(_pool)[convert(is_underlying, uint256)]

    if is_underlying:
        balances = Registry(registry).get_underlying_balances(_pool)
        decimals = Registry(registry).get_underlying_decimals(_pool)
        for x in range(MAX_COINS):
            if convert(x, uint256) == n_coins:
                break
            rates[x] = 10**18
    else:
        balances = Registry(registry).get_balances(_pool)
        decimals = Registry(registry).get_decimals(_pool)
        rates = Registry(registry).get_rates(_pool)

    for x in range(MAX_COINS):
        if convert(x, uint256) == n_coins:
            break
        decimals[x] = 10 ** (18 - decimals[x])

    calculator: address = self.pool_calculator[_pool]
    if calculator == ZERO_ADDRESS:
        calculator = self.default_calculator
    return Calculator(calculator).get_dy(n_coins, balances, amp, fee, rates, decimals, i, j, _amounts)


@payable
@external
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
    is_underlying: bool = False
    i, j, is_underlying = Registry(self.registry).get_coin_indices(_pool, _from, _to)  # dev: no market

    # record initial balance
    initial_balance: uint256 = 0
    if _to == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        initial_balance = self.balance - msg.value
    else:
        initial_balance = ERC20(_to).balanceOf(self)

    # perform / verify input transfer
    if _from == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        assert _amount == msg.value, "Incorrect ETH amount"
    else:
        response: Bytes[32] = raw_call(
            _from,
            concat(
                method_id("transferFrom(address,address,uint256)"),
                convert(msg.sender, bytes32),
                convert(self, bytes32),
                convert(_amount, bytes32),
            ),
            max_outsize=32,
        )
        if len(response) != 0:
            assert convert(response, bool)

    # approve input token
    if not self.is_approved[_from][_pool]:
        response: Bytes[32] = raw_call(
            _from,
            concat(
                method_id("approve(address,uint256)"),
                convert(_pool, bytes32),
                convert(MAX_UINT256, bytes32),
            ),
            max_outsize=32,
        )
        if len(response) != 0:
            assert convert(response, bool)
        self.is_approved[_from][_pool] = True

    # perform coin exchange
    if is_underlying:
        CurvePool(_pool).exchange_underlying(i, j, _amount, _expected, value=msg.value)
    else:
        CurvePool(_pool).exchange(i, j, _amount, _expected, value=msg.value)

    # perform output transfer
    received: uint256 = 0
    if _to == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        received = self.balance - initial_balance
        raw_call(msg.sender, b"", value=received)
    else:
        received = ERC20(_to).balanceOf(self) - initial_balance
        response: Bytes[32] = raw_call(
            _to,
            concat(
                method_id("transfer(address,uint256)"),
                convert(msg.sender, bytes32),
                convert(received, bytes32),
            ),
            max_outsize=32,
        )
        if len(response) != 0:
            assert convert(response, bool)

    log TokenExchange(msg.sender, _pool, _from, _to, _amount, received)

    return True


@view
@external
def get_calculator(_pool: address) -> address:
    """
    @notice Set calculator contract
    @dev Used to calculate `get_dy` for a pool
    @param _pool Pool address
    @return `CurveCalc` address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    calculator: address = self.pool_calculator[_pool]
    if calculator == ZERO_ADDRESS:
        return self.default_calculator
    else:
        return calculator


@external
def set_calculator(_pool: address, _calculator: address):
    """
    @notice Set calculator contract
    @dev Used to calculate `get_dy` for a pool
    @param _pool Pool address
    @param _calculator `CurveCalc` address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    if _pool == ZERO_ADDRESS:
        self.default_calculator = _calculator
    else:
        self.pool_calculator[_pool] = _calculator


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


@external
def claim_balance(_token: address):
    """
    @notice Transfer an ERC20 or ETH balance held by this contract
    @dev The entire balance is transferred to `self.admin`
    @param _token Token address
    """
    assert msg.sender == self.admin  # dev: admin-only function

    if _token == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        raw_call(msg.sender, b"", value=self.balance)
    else:
        amount: uint256 = ERC20(_token).balanceOf(self)
        response: Bytes[32] = raw_call(
            _token,
            concat(
                method_id("transfer(address,uint256)"),
                convert(msg.sender, bytes32),
                convert(amount, bytes32),
            ),
            max_outsize=32,
        )
        if len(response) != 0:
            assert convert(response, bool)
