# @version 0.2.8
"""
@title Curve Registry Calculator
@license (c) Curve.Fi, 2020
@author Curve.Fi
@notice Bulk calculator of prices for stablecoin-to-stablecoin pools for metapools
"""

from vyper.interfaces import ERC20


interface Curve:
    def coins(i: uint256) -> address: view
    def balances(i: uint256) -> uint256: view
    def get_virtual_price() -> uint256: view
    def calc_token_amount(amounts: uint256[N_COINS], deposit: bool) -> uint256: view
    def calc_withdraw_one_coin(_token_amount: uint256, i: int128) -> uint256: view
    def fee() -> uint256: view
    def A_precise() -> uint256: view
    def get_dy(i: int128, j: int128, dx: uint256) -> uint256: view
    def get_dy_underlying(i: int128, j: int128, dx: uint256) -> uint256: view
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): nonpayable
    def add_liquidity(amounts: uint256[N_COINS], min_mint_amount: uint256): nonpayable
    def remove_liquidity_one_coin(_token_amount: uint256, i: int128, min_amount: uint256): nonpayable

interface CurveBase:
    def coins(i: uint256) -> address: view
    def get_virtual_price() -> uint256: view
    def calc_token_amount(amounts: uint256[BASE_N_COINS], deposit: bool) -> uint256: view
    def calc_withdraw_one_coin(_token_amount: uint256, i: int128) -> uint256: view
    def fee() -> uint256: view
    def A_precise() -> uint256: view
    def get_dy(i: int128, j: int128, dx: uint256) -> uint256: view
    def get_dy_underlying(i: int128, j: int128, dx: uint256) -> uint256: view
    def exchange(i: int128, j: int128, dx: uint256, min_dy: uint256): nonpayable
    def add_liquidity(amounts: uint256[BASE_N_COINS], min_mint_amount: uint256): nonpayable
    def remove_liquidity_one_coin(_token_amount: uint256, i: int128, min_amount: uint256): nonpayable
    def base_virtual_price() -> uint256: view


MAX_COINS: constant(int128) = 8
INPUT_SIZE: constant(int128) = 100
FEE_DENOMINATOR: constant(uint256) = 10 ** 10
A_PRECISION: constant(uint256) = 100

BASE_N_COINS: constant(int128) = 3
N_COINS: constant(int128) = 2


base_pool: public(address)
meta_pool: public(address)
base_token: public(address)


@external
def __init__(_base_pool: address, _base_token: address, _meta_pool: address):
    self.base_pool = _base_pool
    self.meta_pool = _meta_pool
    self.base_token = _base_token


@pure
@internal
def get_D(n_coins: uint256, xp: uint256[MAX_COINS], amp: uint256) -> uint256:
    """
    @notice Calculating the invariant (D)
    @param n_coins Number of coins in the pool
    @param xp Array with coin balances made into the same (1e18) digits
    @param amp Amplification coefficient
    @return The value of invariant
    """
    S: uint256 = 0
    for _x in xp:
        if _x == 0:
            break
        S += _x
    if S == 0:
        return 0

    Dprev: uint256 = 0
    D: uint256 = S
    Ann: uint256 = amp * n_coins
    for _i in range(255):
        D_P: uint256 = D
        for _x in xp:
            if _x == 0:
                break
            D_P = D_P * D / (_x * n_coins)  # If division by 0, this will be borked: only withdrawal will work. And that is good
        Dprev = D
        D = (Ann * S / A_PRECISION + D_P * n_coins) * D / ((Ann - A_PRECISION) * D / A_PRECISION + (n_coins + 1) * D_P)
        # Equality with the precision of 1
        if D > Dprev:
            if D - Dprev <= 1:
                break
        else:
            if Dprev - D <= 1:
                break
    return D


@pure
@internal
def get_y(D: uint256, n_coins: uint256, xp: uint256[MAX_COINS], amp: uint256,
          i: int128, j: int128, x: uint256) -> uint256:
    """
    @notice Bulk-calculate new balance of coin j given a new value of coin i
    @param D The Invariant
    @param n_coins Number of coins in the pool
    @param xp Array with coin balances made into the same (1e18) digits
    @param amp Amplification coefficient
    @param i Index of the changed coin (trade in)
    @param j Index of the other changed coin (trade out)
    @param x Amount of coin i (trade in)
    @return Amount of coin j (trade out)
    """
    n_coins_int: int128 = convert(n_coins, int128)
    assert (i != j) and (i >= 0) and (j >= 0) and (i < n_coins_int) and (j < n_coins_int)

    Ann: uint256 = amp * n_coins

    _x: uint256 = 0
    S_: uint256 = 0
    c: uint256 = D
    for _i in range(MAX_COINS):
        if _i == n_coins_int:
            break
        if _i == i:
            _x = x
        elif _i != j:
            _x = xp[_i]
        else:
            continue
        S_ += _x
        c = c * D / (_x * n_coins)
    c = c * D  * A_PRECISION / (Ann * n_coins)
    b: uint256 = S_ + D * A_PRECISION / Ann  # - D
    y_prev: uint256 = 0
    y: uint256 = D
    for _i in range(255):
        y_prev = y
        y = (y*y + c) / (2 * y + b - D)
        # Equality with the precision of 1
        if y > y_prev:
            if y - y_prev <= 1:
                break
        else:
            if y_prev - y <= 1:
                break

    return y


@pure
@internal
def get_y_D(n_coins: uint256, A_: uint256, i: int128, xp: uint256[MAX_COINS], D: uint256) -> uint256:
    """
    Calculate x[i] if one reduces D from being calculated for xp to D

    Done by solving quadratic equation iteratively.
    x_1**2 + x1 * (sum' - (A*n**n - 1) * D / (A * n**n)) = D ** (n + 1) / (n ** (2 * n) * prod' * A)
    x_1**2 + b*x_1 = c

    x_1 = (x_1**2 + c) / (2*x_1 + b)
    """
    # x in the input is converted to the same price/precision
    n_coins_int: int128 = convert(n_coins, int128)

    assert i >= 0  # dev: i below zero
    assert i < n_coins_int  # dev: i above N_COINS

    S_: uint256 = 0
    _x: uint256 = 0
    y_prev: uint256 = 0

    c: uint256 = D
    Ann: uint256 = A_ * n_coins

    for _i in range(MAX_COINS):
        if _i == n_coins_int:
            break
        if _i != i:
            _x = xp[_i]
        else:
            continue
        S_ += _x
        c = c * D / (_x * n_coins)
    c = c * D * A_PRECISION / (Ann * n_coins)
    b: uint256 = S_ + D * A_PRECISION / Ann
    y: uint256 = D
    for _i in range(255):
        y_prev = y
        y = (y*y + c) / (2 * y + b - D)
        # Equality with the precision of 1
        if y > y_prev:
            if y - y_prev <= 1:
                break
        else:
            if y_prev - y <= 1:
                break
    return y


@view
@external
def get_dy(n_coins: uint256, balances: uint256[MAX_COINS], _amp: uint256, fee: uint256,
           rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS],
           i: int128, j: int128, dx: uint256[INPUT_SIZE]) -> uint256[INPUT_SIZE]:
    """
    @notice Bulk-calculate amount of coin j given in exchange for coin i
    @param n_coins Number of coins in the pool
    @param balances Array with coin balances
    @param _amp Amplification coefficient (unused because it uses no precision)
    @param fee Pool's fee at 1e10 basis
    @param rates Array with rates for "lent out" tokens
    @param precisions Precision multipliers to get the coin to 1e18 basis
    @param i Index of the changed coin (trade in)
    @param j Index of the other changed coin (trade out)
    @param dx Array of values of coin i (trade in)
    @return Array of values of coin j (trade out)
    """

    # For metapools, balances are only relevant for non-underlying variant
    # Underlying and non-underlying are chosen based on n_coins

    xp: uint256[MAX_COINS] = balances
    ratesp: uint256[MAX_COINS] = precisions
    for k in range(MAX_COINS):
        xp[k] = xp[k] * rates[k] * precisions[k] / 10 ** 18
        ratesp[k] *= rates[k]
    dy: uint256[INPUT_SIZE] = dx
    amp: uint256 = Curve(self.meta_pool).A_precise()

    if n_coins == N_COINS:
        # Metapool with the pool token
        D: uint256 = self.get_D(n_coins, xp, amp)
        for k in range(INPUT_SIZE):
            if dx[k] == 0:
                break
            else:
                x_after_trade: uint256 = dx[k] * ratesp[i] / 10 ** 18 + xp[i]
                dy[k] = self.get_y(D, n_coins, xp, amp, i, j, x_after_trade)
                dy[k] = (xp[j] - dy[k] - 1) * 10 ** 18 / ratesp[j]
                dy[k] -= dy[k] * fee / FEE_DENOMINATOR

    elif n_coins == N_COINS + BASE_N_COINS - 1:
        _base_pool: address = self.base_pool
        xp_base: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
        v_price: uint256 = CurveBase(_base_pool).base_virtual_price()
        ratesp_base: uint256[MAX_COINS] = ratesp 
        for k in range(BASE_N_COINS):
            xp_base[k] = xp[N_COINS+k-1]
            ratesp_base[k] = ratesp[N_COINS+k-1]
        xp[N_COINS-1] = Curve(self.meta_pool).balances(N_COINS-1) * v_price / 10**18
        ratesp[N_COINS-1] = v_price
        xp[N_COINS] = 0
        ratesp[N_COINS] = 0
        amp_base: uint256 = CurveBase(_base_pool).A_precise()
        D_base_0: uint256 = self.get_D(BASE_N_COINS, xp_base, amp_base)
        D: uint256 = self.get_D(N_COINS, xp, amp)
        base_fee: uint256 = CurveBase(_base_pool).fee()
        base_supply: uint256 = 0
        if i == 0 or j == 0:
            base_fee = base_fee * BASE_N_COINS / (4 * (BASE_N_COINS - 1))
            base_supply = ERC20(self.base_token).totalSupply()
        # 0 -> ... - swap inside, then withdraw from base
        # ... -> 0 - deposit to base, then swap
        # both i, j >= 1 - swap in base

        for k in range(INPUT_SIZE):
            if dx[k] == 0:
                break
            else:
                if i == 0:
                    # swap
                    x_after_trade: uint256 = dx[k] * ratesp[0] / 10**18 + xp[0]
                    _dy: uint256 = self.get_y(D, N_COINS, xp, amp, 0, 1, x_after_trade)
                    _dy = (xp[1] - _dy - 1) * 10**18 / ratesp[1]
                    _dy -= _dy * fee / FEE_DENOMINATOR
                    # withdraw_one_coin: _dy tokens, j-1 is the coin
                    D1: uint256 = D_base_0 - _dy * D_base_0 / base_supply
                    xp_reduced: uint256[MAX_COINS] = xp_base
                    _y: uint256 = self.get_y_D(BASE_N_COINS, amp_base, j-1, xp_base, D1)
                    for l in range(BASE_N_COINS):
                        dx_expected: uint256 = xp_base[l]
                        if l == j-1:
                            dx_expected = dx_expected*D1/D_base_0 - _y
                        else:
                            dx_expected = dx_expected - dx_expected*D1/D_base_0
                        xp_reduced[l] -= base_fee * dx_expected / FEE_DENOMINATOR
                    dy[k] = xp_reduced[j-1] - self.get_y_D(BASE_N_COINS, amp_base, j-1, xp_reduced, D1)
                    dy[k] = (dy[k] - 1) / precisions[j]

                elif j == 0:
                    # deposit to base pool (calc_token_amount)
                    new_balances: uint256[MAX_COINS] = xp_base
                    new_balances[i-1] += dx[k] * ratesp_base[i-1] / 10**18
                    # invariant after deposit
                    D1: uint256 = self.get_D(BASE_N_COINS, new_balances, amp_base)
                    # take fees into account
                    for l in range(BASE_N_COINS):
                        ideal_balance: uint256 = D1 * xp_base[l] / D_base_0
                        difference: uint256 = 0
                        if ideal_balance > new_balances[l]:
                            difference = ideal_balance - new_balances[l]
                        else:
                            difference = new_balances[l] - ideal_balance
                        new_balances[l] -= base_fee * difference / FEE_DENOMINATOR
                    D2: uint256 = self.get_D(BASE_N_COINS, new_balances, amp_base)
                    dx_meta: uint256 = base_supply * (D2 - D_base_0) / D_base_0
                    # swap dx_meta to coin j
                    x_after_trade: uint256 = dx_meta * v_price / 10**18 + xp[1]
                    dy[k] = self.get_y(D, N_COINS, xp, amp, 1, 0, x_after_trade)
                    dy[k] = (xp[0] - dy[k] - 1) * 10**18 / ratesp[0]
                    dy[k] -= dy[k] * fee / FEE_DENOMINATOR
                else:
                    x_after_trade: uint256 = dx[k] * ratesp_base[i-1] / 10**18 + xp_base[i-1]
                    dy[k] = self.get_y(D_base_0, BASE_N_COINS, xp_base, amp_base, i-1, j-1, x_after_trade)
                    dy[k] = (xp_base[j-1] - dy[k] - 1) * 10**18 / ratesp_base[j-1]
                    dy[k] -= dy[k] * base_fee / FEE_DENOMINATOR

    else:
        raise "Unsupported pool size"

    return dy

@view
@external
def get_dx(n_coins: uint256, balances: uint256[MAX_COINS], _amp: uint256, fee: uint256,
           rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS],
           i: int128, j: int128, dy: uint256[INPUT_SIZE]) -> uint256[INPUT_SIZE]:
    """
    @notice Bulk-calculate amount of coin i taken when exchanging for coin j
    @param n_coins Number of coins in the pool
    @param balances Array with coin balances
    @param _amp Amplification coefficient
    @param fee Pool's fee at 1e10 basis
    @param rates Array with rates for "lent out" tokens
    @param precisions Precision multipliers to get the coin to 1e18 basis
    @param i Index of the changed coin (trade in)
    @param j Index of the other changed coin (trade out)
    @param dy Array of values of coin j (trade out)
    @return Array of values of coin i (trade in)
    """
    
    xp: uint256[MAX_COINS] = balances
    ratesp: uint256[MAX_COINS] = precisions
    for k in range(MAX_COINS):
        xp[k] = xp[k] * rates[k] * precisions[k] / 10 ** 18
        ratesp[k] *= rates[k]
    dx: uint256[INPUT_SIZE] = dy
    amp: uint256 = Curve(self.meta_pool).A_precise()

    if n_coins == N_COINS:
        # Metapool with the pool token
        D: uint256 = self.get_D(n_coins, xp, amp)
        for k in range(INPUT_SIZE):
            if dy[k] == 0:
                break
            else:
                y_after_trade: uint256 = xp[j] - dy[k] * ratesp[j] / 10 ** 18 * FEE_DENOMINATOR / (FEE_DENOMINATOR - fee)
                dx[k] = self.get_y(D, n_coins, xp, amp, j, i, y_after_trade)
                dx[k] = (dx[k] - xp[i]) * 10 ** 18 / ratesp[i]

    elif n_coins == N_COINS + BASE_N_COINS - 1:
        _base_pool: address = self.base_pool
        xp_base: uint256[MAX_COINS] = empty(uint256[MAX_COINS])
        v_price: uint256 = CurveBase(_base_pool).base_virtual_price()
        ratesp_base: uint256[MAX_COINS] = ratesp 
        for k in range(BASE_N_COINS):
            xp_base[k] = xp[N_COINS+k-1]
            ratesp_base[k] = ratesp[N_COINS+k-1]
        xp[N_COINS-1] = Curve(self.meta_pool).balances(N_COINS-1) * v_price / 10**18
        ratesp[N_COINS-1] = v_price
        xp[N_COINS] = 0
        ratesp[N_COINS] = 0
        amp_base: uint256 = CurveBase(_base_pool).A_precise()
        D_base_0: uint256 = self.get_D(BASE_N_COINS, xp_base, amp_base)
        D: uint256 = self.get_D(N_COINS, xp, amp)
        base_fee: uint256 = CurveBase(_base_pool).fee()
        base_supply: uint256 = 0
        if i == 0 or j == 0:
            base_fee = base_fee * BASE_N_COINS / (4 * (BASE_N_COINS - 1))
            base_supply = ERC20(self.base_token).totalSupply()
        # ... -> 0 - swap inside, withdraw from base
        # 0 -> ... - withdraw from base, swap inside
        # both i, j >= 1 - swap in base

        for k in range(INPUT_SIZE):
            if dy[k] == 0:
                break
            else:
                if j == 0:
                    y_after_trade: uint256 = xp[j] - dy[k] * ratesp[j] / 10**18 * FEE_DENOMINATOR / (FEE_DENOMINATOR - fee)
                    _dx: uint256 = self.get_y(D, N_COINS, xp, amp, 0, 1, y_after_trade)
                    _dx = (_dx - xp[1] - 1) * 10**18 / ratesp[1]
                    D1: uint256 = D_base_0 + _dx * D_base_0 / base_supply
                    new_balances: uint256[MAX_COINS] = xp_base
                    _y: uint256 = self.get_y_D(
                        BASE_N_COINS, amp_base, i-1, xp_base, D1)
                    for l in range(BASE_N_COINS):
                        dx_expected: uint256 = xp_base[l]
                        if l == i-1:
                            dx_expected = _y - dx_expected*D1/D_base_0
                        else:
                            dx_expected = dx_expected*D1/D_base_0 - dx_expected
                        new_balances[l] -= base_fee * \
                            dx_expected / FEE_DENOMINATOR
                    dx[k] = self.get_y_D(BASE_N_COINS, amp_base,
                                    i-1, new_balances, D1) - new_balances[i-1]
                    dx[k] = (dx[k] - 1) / precisions[i]
                elif i == 0:
                    # # coin j-1 from base pool is withdrawn 
                    new_balances: uint256[MAX_COINS] = xp_base
                    # new_balances[j-1] -= dy[k] * ratesp_base[j-1] / 10**18
                    # # invariant after withdrawal
                    # D1: uint256 = self.get_D(BASE_N_COINS, new_balances, amp_base)
                    # # take fees into account
                    # for l in range(BASE_N_COINS):
                    #     ideal_balance: uint256 = D1 * xp_base[l] / D_base_0
                    #     difference: uint256 = 0
                    #     if ideal_balance > new_balances[l]:
                    #         difference = ideal_balance - new_balances[l]
                    #     else:
                    #         difference = new_balances[l] - ideal_balance
                    #     new_balances[l] -= base_fee * difference / FEE_DENOMINATOR
                    # D2: uint256 = self.get_D(BASE_N_COINS, new_balances, amp_base)
                    # dx_meta: uint256 = base_supply * (D_base_0 - D2) / D_base_0
                    # # swap dx_meta to coin i
                    # y_after_trade: uint256 = xp[1] - dx_meta * v_price / 10**18 * FEE_DENOMINATOR / (FEE_DENOMINATOR - fee)
                    # dx[k] = self.get_y(D, N_COINS, xp, amp, 1, 0, y_after_trade)
                    # dx[k] = (dx[k] - xp[0] - 1) * 10**18 / ratesp[0]
                else:
                    # swap in base pool
                    y_after_trade: uint256 = xp_base[j-1] - dy[k] * ratesp_base[j-1] / 10**18 * FEE_DENOMINATOR / (FEE_DENOMINATOR - fee)
                    dx[k] = self.get_y(D_base_0, BASE_N_COINS, xp_base, amp_base, j-1, i-1, y_after_trade)
                    dx[k] = (dx[k] - xp_base[i-1] - 1) * 10 ** 18 / ratesp_base[i-1]
    else:
        raise "Unsupported pool size"

    return dx

