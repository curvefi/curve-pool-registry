# (c) Curve.Fi, 2020
# Stateless bulk calculator of prices for stablecoin-to-stablecoin pools

MAX_COINS: constant(int128) = 8
INPUT_SIZE: constant(int128) = 50
FEE_DENOMINATOR: constant(uint256) = 10 ** 10


@private
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
        S += _x
    if S == 0:
        return 0

    Dprev: uint256 = 0
    D: uint256 = S
    Ann: uint256 = amp * n_coins
    for _i in range(255):
        D_P: uint256 = D
        for _x in xp:
            D_P = D_P * D / (_x * n_coins)  # If division by 0, this will be borked: only withdrawal will work. And that is good
        Dprev = D
        D = (Ann * S + D_P * n_coins) * D / ((Ann - 1) * D + (n_coins + 1) * D_P)
        # Equality with the precision of 1
        if D > Dprev:
            if D - Dprev <= 1:
                break
        else:
            if Dprev - D <= 1:
                break
    return D


@private
def get_y(n_coins: int128, xp: uint256[MAX_COINS], amp: uint256,
          i: int128, j: int128, x: uint256[INPUT_SIZE]) -> uint256[INPUT_SIZE]:
    """
    @notice Bulk-calculate new balance of coin j given a new value of coin i
    @param n_coins Number of coins in the pool
    @param xp Array with coin balances made into the same (1e18) digits
    @param amp Amplification coefficient
    @param i Index of the changed coin (trade in)
    @param j Index of the other changed coin (trade out)
    @param x Array of values of coin i (trade in)
    @return Array of values of coin j (trade out)
    """
    assert (i != j) and (i >= 0) and (j >= 0) and (i < n_coins) and (j < n_coins)
    n_coins_256: uint256 = convert(n_coins, uint256)

    D: uint256 = self.get_D(n_coins_256, xp, amp)
    Ann: uint256 = amp * n_coins_256
    y_out: uint256[INPUT_SIZE] = x  # This is a hack: in Vyper 0.2 should be empty(uint256)

    for _input_id in range(INPUT_SIZE):
        if x[_input_id] == 0:
            break
        _x: uint256 = 0
        S_: uint256 = 0
        c: uint256 = D
        for _i in range(MAX_COINS):
            if _i >= n_coins:
                break
            if _i == i:
                _x = x[_input_id]
            elif _i != j:
                _x = xp[_i]
            else:
                continue
            S_ += _x
            c = c * D / (_x * n_coins_256)
        c = c * D / (Ann * n_coins_256)
        b: uint256 = S_ + D / Ann  # - D
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
        y_out[_input_id] = y

    return y_out


@public
def get_dy(n_coins: int128, balances: uint256[MAX_COINS], amp: uint256, fee: uint256,
           rates: uint256[MAX_COINS], precisions: uint256[MAX_COINS],
           underlying: bool,
           i: int128, j: int128, dx: uint256[INPUT_SIZE]) -> uint256[INPUT_SIZE]:
    """
    @notice Bulk-calculate amount of of coin j given in exchange for coin i
    @param n_coins Number of coins in the pool
    @param balances Array with coin balances
    @param amp Amplification coefficient
    @param fee Pool's fee at 1e10 basis
    @param rates Array with rates for "lent out" tokens
    @param precisions Precision multipliers to get the coin to 1e18 basis
    @param underlying Whether the coin is in raw or lent-out form
    @param i Index of the changed coin (trade in)
    @param j Index of the other changed coin (trade out)
    @param dx Array of values of coin i (trade in)
    @return Array of values of coin j (trade out)
    """

    xp: uint256[MAX_COINS] = balances
    ratesp: uint256[MAX_COINS] = precisions
    for k in range(MAX_COINS):
        xp[k] = xp[k] * rates[k] * precisions[k] / 10 ** 18
        if not underlying:
            ratesp[k] = ratesp[k] * rates[k] / 10 ** 18

    x_after_trade: uint256[INPUT_SIZE] = dx
    for k in range(INPUT_SIZE):
        if dx[k] == 0:
            break
        x_after_trade[k] *= ratesp[i]
        x_after_trade[k] += xp[i]

    dy: uint256[INPUT_SIZE] = self.get_y(
        n_coins, xp, amp, i, j, x_after_trade)
    for k in range(INPUT_SIZE):
        if dx[k] == 0:
            dy[k] = 0  # zero the garbage (can do better with Vyper 0.2)
        else:
            dy[k] = (xp[j] - dy[k] - 1) / ratesp[j]
            dy[k] -= dy[k] * fee / FEE_DENOMINATOR

    return dy
