import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS
from brownie.exceptions import VirtualMachineError


@pytest.fixture(scope="module")
def swap1(PoolMockV2, underlying_coins, alice, bob):
    swap = PoolMockV2.deploy(4, underlying_coins, [ZERO_ADDRESS] * 4, 70, 5000000, {"from": alice})
    bob.transfer(swap, "10 ether")
    yield swap


@pytest.fixture(scope="module")
def swap2(PoolMockV2, underlying_coins, alice, bob):
    swap = PoolMockV2.deploy(
        3, underlying_coins[1:] + [ZERO_ADDRESS], [ZERO_ADDRESS] * 4, 70, 3000000, {"from": alice}
    )
    bob.transfer(swap, "10 ether")
    yield swap


@pytest.fixture(scope="module")
def swap3(PoolMockV2, underlying_coins, alice):
    yield PoolMockV2.deploy(
        2, underlying_coins[:2] + [ZERO_ADDRESS] * 2, [ZERO_ADDRESS] * 4, 70, 0, {"from": alice}
    )


@pytest.fixture(scope="module")
def registry(ERC20, Registry, provider, gauge_controller, alice, swap1, swap2, swap3, lp_token):
    registry = Registry.deploy(provider, gauge_controller, {"from": alice})
    provider.set_address(0, registry, {"from": alice})

    for swap, n_coins in ((swap1, 4), (swap2, 3), (swap3, 2)):
        token = ERC20.deploy("", "", 18, {"from": alice})
        registry.add_pool_without_underlying(
            swap,
            n_coins,
            token,
            "0x00",
            0,
            0,  # use rates
            hasattr(swap, "initial_A"),
            False,
            "",
            {"from": alice},
        )

    yield registry


@pytest.fixture(scope="module")
def factory(pm, alice):
    yield pm("curvefi/curve-factory@2.0.0").Factory.deploy({"from": alice})


@pytest.fixture(scope="module")
def registry_swap(Swaps, alice, registry, provider, factory, calculator, underlying_coins):
    contract = Swaps.deploy(provider, calculator, {"from": alice})
    provider.add_new_id(provider, "Filler", {"from": alice})
    provider.add_new_id(contract, "Pool Swaps", {"from": alice})
    provider.add_new_id(factory, "Factory", {"from": alice})
    contract.update_registry_address({"from": alice})

    for coin in underlying_coins:
        if coin != ETH_ADDRESS:
            coin.approve(contract, 2 ** 256 - 1, {"from": alice})
            coin._mint_for_testing(alice, 10 ** 18, {"from": alice})

    yield contract


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_get_best_rate(registry_swap, swap1, swap2, swap3, underlying_coins, send, recv):
    send = underlying_coins[send]
    recv = underlying_coins[recv]

    best_swap = None
    best_rate = 0
    for swap in (swap1, swap2, swap3):
        try:
            rate = registry_swap.get_exchange_amount(swap, send, recv, 10 ** 18)
            if rate > best_rate:
                best_rate = rate
                best_swap = swap
        except VirtualMachineError:
            pass

    assert registry_swap.get_best_rate(send, recv, 10 ** 18) == (best_swap, best_rate)


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_get_best_rate_with_exclusion(
    registry_swap, swap1, swap2, swap3, underlying_coins, send, recv
):
    send = underlying_coins[send]
    recv = underlying_coins[recv]
    exclude_list = [swap1] + [ZERO_ADDRESS] * 7

    best_swap = ZERO_ADDRESS
    best_rate = 0
    for swap in (swap1, swap2, swap3):
        try:
            rate = registry_swap.get_exchange_amount(swap, send, recv, 10 ** 18)
            if rate > best_rate and swap not in exclude_list:
                best_rate = rate
                best_swap = swap
        except VirtualMachineError:
            pass

    assert registry_swap.get_best_rate(send, recv, 10 ** 18, exclude_list) == (best_swap, best_rate)


@pytest.mark.params(n_coins=4)
@pytest.mark.itercoins("send", "recv")
def test_exchange_with_best_rate(
    alice, registry_swap, swap1, swap2, swap3, underlying_coins, underlying_decimals, send, recv
):
    amount = 10 ** underlying_decimals[send]

    send = underlying_coins[send]
    recv = underlying_coins[recv]

    best_swap = None
    best_rate = 0
    for swap in (swap1, swap2, swap3):
        try:
            rate = registry_swap.get_exchange_amount(swap, send, recv, amount)
            if rate > best_rate:
                best_rate = rate
                best_swap = swap
        except VirtualMachineError:
            pass

    value = 10 ** 18 if send == ETH_ADDRESS else 0
    tx = registry_swap.exchange_with_best_rate(
        send, recv, amount, 0, {"from": alice, "value": value}
    )

    assert tx.events["TokenExchange"]["pool"] == best_swap
