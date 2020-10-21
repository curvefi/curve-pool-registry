# @version ^0.2.0
"""
@notice Mock Curve metapool for testing
"""

FEE_PRECISION: constant(uint256) = 10**10

interface ERC20Mock:
    def decimals() -> uint256: view
    def balanceOf(_addr: address) -> uint256: view
    def transfer(_to: address, _amount: uint256) -> bool: nonpayable
    def transferFrom(_from: address, _to: address, _amount: uint256) -> bool: nonpayable
    def _mint_for_testing(_to: address, _amount: uint256): nonpayable

n_coins: public(uint256)
n_coins_underlying: uint256
coin_list: address[4]
base_coin_list: address[4]

A: public(uint256)
initial_A: public(uint256)
initial_A_time: public(uint256)
future_A: public(uint256)
future_A_time: public(uint256)

fee: public(uint256)
admin_fee: public(uint256)
future_fee: public(uint256)
future_admin_fee: public(uint256)
future_owner: public(address)

base_pool: public(address)
get_virtual_price: public(uint256)

_balances: uint256[4]

@external
def __init__(
    _n_coins: uint256,
    _n_coins_underlying: uint256,
    _base_pool: address,
    _coin_list: address[4],
    _base_coin_list: address[4],
    _A: uint256,
    _fee: uint256,
):
    self.n_coins = _n_coins
    self.n_coins_underlying = _n_coins_underlying
    self.base_pool = _base_pool
    self.coin_list = _coin_list
    self.base_coin_list = _base_coin_list
    self.A = _A
    self.fee = _fee
    self.get_virtual_price = 10**18


@external
@view
def coins(i: uint256) -> address:
    assert i < self.n_coins  # dev: exceeds n_coins
    return self.coin_list[i]


@external
@view
def base_coins(i: uint256) -> address:
    assert i < self.n_coins_underlying  # dev: exceeds n_coins
    return self.base_coin_list[i]


@external
@view
def balances(i: uint256) -> uint256:
    assert i < self.n_coins
    return self._balances[i]


@internal
@view
def _get_dy(_from: address, _to: address, _dx: uint256) -> uint256:
    _from_precision: uint256 = 0
    _to_precision: uint256 = 0

    if _from == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        _from_precision = 18
    else:
        _from_precision = ERC20Mock(_from).decimals()
    if _to == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        _to_precision = 18
    else:
        _to_precision = ERC20Mock(_to).decimals()

    _dy: uint256 = _dx * (10**_to_precision) / (10**_from_precision)
    _fee: uint256 = _dy * self.fee / FEE_PRECISION

    return _dy - _fee


@external
@view
def get_dy(i: int128, j: int128, dx: uint256) -> uint256:
    return self._get_dy(self.coin_list[i], self.coin_list[j], dx)


@external
@view
def get_dy_underlying(i: int128, j: int128, dx: uint256) -> uint256:
    _from: address = ZERO_ADDRESS
    _to: address = ZERO_ADDRESS

    max_base_coin: int128 = convert(self.n_coins - 1, int128)
    if i <= max_base_coin:
        _from = self.coin_list[i]
    else:
        _from = self.base_coin_list[i-max_base_coin]
    if j <= max_base_coin:
        _to = self.coin_list[j]
    else:
        _to = self.base_coin_list[j-max_base_coin]

    return self._get_dy(_from, _to, dx)


@internal
def _exchange(_sender: address, _from: address, _to: address, dx: uint256, min_dy: uint256):
    dy: uint256 = self._get_dy(_from, _to, dx)
    assert dy >= min_dy, "Exchange resulted in fewer coins than expected"

    if _from != 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        _response: Bytes[32] = raw_call(
            _from,
            concat(
                method_id("transferFrom(address,address,uint256)"),
                convert(_sender, bytes32),
                convert(self, bytes32),
                convert(dx, bytes32),
            ),
            max_outsize=32,
        )
        if len(_response) > 0:
            assert convert(_response, bool)

    if _to == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        send(_sender, dy)
    else:
        ERC20Mock(_to)._mint_for_testing(self, dy)
        _response: Bytes[32] = raw_call(
            _to,
            concat(
                method_id("transfer(address,uint256)"),
                convert(_sender, bytes32),
                convert(dy, bytes32),
            ),
            max_outsize=32,
        )
        if len(_response) > 0:
            assert convert(_response, bool)


@external
@payable
@nonreentrant('lock')
def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256):
    _from: address = self.coin_list[i]
    if _from == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        assert msg.value == dx
    else:
        assert msg.value == 0

    self._exchange(msg.sender, _from, self.coin_list[j], dx, min_dy)


@external
@payable
@nonreentrant('lock')
def exchange_underlying(i: int128, j: int128, dx: uint256, min_dy: uint256):
    _from: address = ZERO_ADDRESS
    _to: address = ZERO_ADDRESS

    max_base_coin: int128 = convert(self.n_coins - 1, int128)
    if i < max_base_coin:
        _from = self.coin_list[i]
    else:
        _from = self.base_coin_list[i-max_base_coin]
    if j < max_base_coin:
        _to = self.coin_list[j]
    else:
        _to = self.base_coin_list[j-max_base_coin]

    if _from == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        assert msg.value == dx
    else:
        assert msg.value == 0

    self._exchange(msg.sender, _from, _to, dx, min_dy)


# testing functions

@external
def _set_A(
    _A: uint256,
    _initial_A: uint256,
    _initial_A_time: uint256,
    _future_A: uint256,
    _future_A_time: uint256
):
    self.A = _A
    self.initial_A = _initial_A
    self.initial_A_time = _initial_A_time
    self.future_A = _future_A
    self.future_A_time = _future_A_time


@external
def _set_fees_and_owner(
    _fee: uint256,
    _admin_fee: uint256,
    _future_fee: uint256,
    _future_admin_fee: uint256,
    _future_owner: address
):
    self.fee = _fee
    self.admin_fee = _admin_fee
    self.future_fee = _future_fee
    self.future_admin_fee = _future_admin_fee
    self.future_owner = _future_owner

@external
def _set_balances(_new_balances: uint256[4]):
    self._balances = _new_balances


@external
def _set_virtual_price(_value: uint256):
    self.get_virtual_price = _value


@external
@payable
def __default__():
    pass
