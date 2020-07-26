"""
@notice Mock Curve pool for testing
"""

FEE_PRECISION: constant(uint256) = 10**10

interface ERC20Mock:
    def decimals() -> uint256: view
    def balanceOf(_addr: address) -> uint256: view
    def transfer(_to: address, _amount: uint256) -> bool: nonpayable
    def transferFrom(_from: address, _to: address, _amount: uint256) -> bool: nonpayable
    def _mint_for_testing(_amount: uint256): nonpayable

n_coins: public(int128)
coin_list: address[4]
underlying_coin_list: address[4]
returns_none: HashMap[address, bool]

A: public(uint256)
fee: public(uint256)


@external
def __init__(
    _n_coins: int128,
    _coin_list: address[4],
    _underlying_coin_list: address[4],
    _returns_none: address[4],
    _A: uint256,
    _fee: uint256,
):
    self.n_coins = _n_coins
    self.coin_list = _coin_list
    self.underlying_coin_list = _underlying_coin_list
    self.A = _A
    self.fee = _fee
    for _addr in _returns_none:
        if _addr == ZERO_ADDRESS:
            break
        self.returns_none[_addr] = True


@external
@view
def coins(i: int128) -> address:
    assert i < self.n_coins  # dev: exceeds n_coins
    return self.coin_list[i]


@external
@view
def underlying_coins(i: int128) -> address:
    assert i < self.n_coins  # dev: exceeds n_coins
    return self.underlying_coin_list[i]


@external
@view
def balances(i: int128) -> uint256:
    return ERC20Mock(self.coin_list[i]).balanceOf(self)


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
    return self._get_dy(self.underlying_coin_list[i], self.underlying_coin_list[j], dx)


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
        ERC20Mock(_to)._mint_for_testing(dy)
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
    _from: address = self.underlying_coin_list[i]
    if _from == 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE:
        assert msg.value == dx
    else:
        assert msg.value == 0

    self._exchange(msg.sender, _from, self.underlying_coin_list[j], dx, min_dy)


# testing functions

@external
def _set_A(_value: uint256):
    self.A = _value


@external
def _set_fee(_value: uint256):
    self.fee = _value


@external
@payable
def __default__():
    pass
