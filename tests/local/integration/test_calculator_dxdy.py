from brownie.test import given, strategy
from hypothesis import Phase, settings


@given(
    st_precision=strategy("uint[4]", min_value=6, max_value=18),
    st_balance=strategy("uint[4]", min_value=10 ** 21, max_value=10 ** 23, unique=True),
    st_rates=strategy("uint[4]", min_value=10 ** 18, max_value=10 ** 19, unique=True),
    st_idx=strategy("uint[2]", max_value=3, unique=True),
    dx=strategy("uint", min_value=10 ** 19, max_value=10 ** 20),
)
@settings(phases=[Phase.reuse, Phase.generate])
def test_dy_dx(calculator, st_precision, st_balance, st_rates, st_idx, dx):
    precision = [10 ** (18 - i) for i in st_precision] + [0, 0, 0, 0]
    balances = [st_balance[i] // precision[i] for i in range(4)] + [0, 0, 0, 0]
    rates = st_rates + [0, 0, 0, 0]
    dx //= precision[st_idx[0]]

    dy = calculator.get_dy(
        4, balances, 100, 4000000, rates, precision, st_idx[0], st_idx[1], [dx] + [0] * 99
    )[0]

    dx_final = calculator.get_dx(
        4, balances, 100, 4000000, rates, precision, st_idx[0], st_idx[1], dy
    )

    assert min(dx, dx_final) / max(dx, dx_final) >= 0.9995


@given(
    st_precision=strategy("uint[4]", min_value=6, max_value=18),
    st_balance=strategy("uint[4]", min_value=10 ** 21, max_value=10 ** 23, unique=True),
    st_rates=strategy("uint[4]", min_value=10 ** 18, max_value=10 ** 19, unique=True),
    st_idx=strategy("uint[2]", max_value=3, unique=True),
    dy=strategy("uint", min_value=10 ** 19, max_value=10 ** 20),
)
@settings(phases=[Phase.reuse, Phase.generate])
def test_dx_dy(calculator, st_precision, st_balance, st_rates, st_idx, dy):
    precision = [10 ** (18 - i) for i in st_precision] + [0, 0, 0, 0]
    balances = [st_balance[i] // precision[i] for i in range(4)] + [0, 0, 0, 0]
    rates = st_rates + [0, 0, 0, 0]
    dy //= precision[st_idx[1]]

    dx = calculator.get_dx(4, balances, 100, 4000000, rates, precision, st_idx[0], st_idx[1], dy)

    dy_final = calculator.get_dy(
        4, balances, 100, 4000000, rates, precision, st_idx[0], st_idx[1], [dx] + [0] * 99
    )[0]

    assert min(dy, dy_final) / max(dy, dy_final) >= 0.9995
