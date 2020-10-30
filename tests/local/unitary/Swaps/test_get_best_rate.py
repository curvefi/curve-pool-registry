import pytest

from brownie.exceptions import VirtualMachineError

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module")
def swap1(PoolMockV2, underlying_coins, alice):
    yield PoolMockV2.deploy(
        4, underlying_coins, [ZERO_ADDRESS] * 4, 70, 5000000, {"from": alice}
    )


@pytest.fixture(scope="module")
def swap2(PoolMockV2, underlying_coins, alice):
    yield PoolMockV2.deploy(
        3, underlying_coins[1:] + [ZERO_ADDRESS], [ZERO_ADDRESS] * 4, 70, 3000000, {"from": alice}
    )


@pytest.fixture(scope="module")
def swap3(PoolMockV2, underlying_coins, alice):
    yield PoolMockV2.deploy(
        2, underlying_coins[:2] + [ZERO_ADDRESS] * 2, [ZERO_ADDRESS] * 4, 70, 0, {"from": alice}
    )


@pytest.fixture(scope="module")
def registry(ERC20, Registry, provider, gauge_controller, alice, swap1, swap2, swap3, lp_token):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})

    for swap, n_coins in ((swap1, 4), (swap2, 3), (swap3, 2)):
        token = ERC20.deploy("", "", 18, {'from': alice})
        registry.add_pool_without_underlying(
            swap,
            n_coins,
            token,
            "0x00",
            0,
            0,  # use rates
            hasattr(swap, "initial_A"),
            False,
            {"from": alice},
        )

    yield registry


@pytest.fixture(scope="module")
def registry_swap(Swaps, alice, registry, calculator):
    yield Swaps.deploy(registry, calculator, {'from': alice})


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_get_best_rate(registry_swap, swap1, swap2, swap3, underlying_coins, send, recv):
    send = underlying_coins[send]
    recv = underlying_coins[recv]

    best_swap = None
    best_rate = 0
    for swap in (swap1, swap2, swap3):
        try:
            rate = registry_swap.get_exchange_amount(swap, send, recv, 10**18)
            if rate > best_rate:
                best_rate = rate
                best_swap = swap
        except VirtualMachineError:
            pass

    assert registry_swap.get_best_rate(send, recv, 10**18) == (best_swap, best_rate)
