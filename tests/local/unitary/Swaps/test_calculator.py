import brownie
import pytest
from brownie import ZERO_ADDRESS


def test_admin_only(bob, registry_swap):
    with brownie.reverts("dev: admin-only function"):
        registry_swap.set_calculator(ZERO_ADDRESS, ZERO_ADDRESS, {"from": bob})


def test_default_calculator(alice, registry_swap, calculator):
    assert registry_swap.get_calculator(alice) == calculator
    assert registry_swap.default_calculator() == calculator


def test_set_calculator(alice, bob, registry_swap):
    registry_swap.set_calculator(alice, bob, {"from": alice})

    assert registry_swap.get_calculator(alice) == bob


def test_unset_calculator(alice, bob, registry_swap):
    registry_swap.set_calculator(alice, bob, {"from": alice})
    registry_swap.set_calculator(alice, ZERO_ADDRESS, {"from": alice})

    assert registry_swap.get_calculator(alice) == registry_swap.default_calculator()


def test_set_default_calculator(alice, bob, registry_swap):
    registry_swap.set_default_calculator(bob, {"from": alice})

    assert registry_swap.get_calculator(alice) == bob
    assert registry_swap.default_calculator() == bob


@pytest.mark.no_call_coverage
def test_calculator(accounts, calculator):
    expected = [89743074, 100065, 37501871, 90394938, 114182]
    actual = calculator.get_dy.call(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        0,
        1,
        [89970746, 100274, 37586976, 90624569, 114419] + [0] * 95,
    )

    assert actual[:5] == expected


@pytest.mark.no_call_coverage
def test_dy_dx(accounts, calculator):
    dx = calculator.get_dx(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        0,
        1,
        89970746,
    )
    assert (
        calculator.get_dy(
            2,
            (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
            100,
            4000000,
            (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
            (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
            0,
            1,
            [dx] + [0] * 99,
        )[0]
        == 89970746
    )


@pytest.mark.no_call_coverage
def test_dx_dy(accounts, calculator):
    dy = calculator.get_dy(
        2,
        (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
        100,
        4000000,
        (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
        (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
        0,
        1,
        [89970746] + [0] * 99,
    )[0]
    assert (
        calculator.get_dx(
            2,
            (2241857934, 1895960155, 0, 0, 0, 0, 0, 0),
            100,
            4000000,
            (1000000000000000000, 1000000000000000000, 0, 0, 0, 0, 0, 0),
            (10000000000, 10000000000, 0, 0, 0, 0, 0, 0),
            0,
            1,
            dy,
        )
        == 89970746
    )
