import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_get_coins(registry, swap, n_coins):
    coins = registry.get_coins(swap)
    for i in range(n_coins):
        assert coins[i] == swap.coins(i)

    assert coins[n_coins] == ZERO_ADDRESS
    with brownie.reverts():
        swap.coins(n_coins)


def test_get_decimals(Contract, registry, swap, wrapped_coins):
    decimals = registry.get_decimals(swap)
    for i, coin in enumerate(wrapped_coins):
        assert coin.decimals() == decimals[i]


def test_get_underlying_decimals(Contract, registry, swap, underlying_coins, pool_data):
    decimals = registry.get_underlying_decimals(swap)
    for i, coin in enumerate(underlying_coins):
        if "decimals" in pool_data["coins"][i]:
            assert coin.decimals() == decimals[i]
        else:
            assert decimals[i] == 0


def test_get_virtual_price_from_lp_token(registry, swap, lp_token):
    assert registry.get_virtual_price_from_lp_token(lp_token) == swap.get_virtual_price()


def test_get_rates(registry, swap, wrapped_coins):
    rates = registry.get_rates(swap)
    for i, coin in enumerate(wrapped_coins):
        assert rates[i] == coin._get_rate()


def test_get_balances(registry, swap, n_coins):
    balances = registry.get_balances(swap)
    for i in range(n_coins):
        assert swap.balances(i) == balances[i]


@pytest.mark.skip_meta
def test_get_underlying_balances(registry, swap, n_coins, wrapped_coins, underlying_coins):
    underlying_balances = registry.get_underlying_balances(swap)

    for i in range(n_coins):
        balance = swap.balances(i)
        if wrapped_coins[i] == underlying_coins[i]:
            assert balance == underlying_balances[i]
        else:
            rate = wrapped_coins[i]._get_rate()
            decimals = underlying_coins[i].decimals()
            assert balance * rate // 10 ** decimals == underlying_balances[i]


@pytest.mark.meta
def test_get_underlying_balances_meta(
    bob, registry, swap, base_swap, wrapped_coins, underlying_coins
):
    underlying_balances = registry.get_underlying_balances(swap)

    for i in range(len(wrapped_coins) - 1):
        assert underlying_balances[i] == swap.balances(i)

    idx = len(wrapped_coins) - 1
    base_n_coins = len(underlying_coins) - 1
    lp_token = wrapped_coins[idx]
    lp_balance = swap.balances(idx)

    # some voodoo here - we transfer the balance of the base LP tokens from `swap` to `bob`
    # and then withdraw them from `base_pool` to get the actual underlying amounts
    lp_token.transfer(bob, lp_balance, {"from": swap})
    base_swap.remove_liquidity(lp_balance, [0] * base_n_coins, {"from": bob})

    for i, coin in enumerate(underlying_coins[1:], start=1):
        assert coin.balanceOf(bob) == underlying_balances[i]
