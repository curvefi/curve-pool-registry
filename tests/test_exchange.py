import brownie


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_exchange(accounts, registry, pool_compound, cDAI, cUSDC):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )
    cDAI._mint_for_testing(10**18, {'from': accounts[0]})
    cDAI.approve(registry, 10**18, {'from': accounts[0]})
    expected = registry.get_exchange_amount(pool_compound, cDAI, cUSDC, 10**18)

    registry.exchange(pool_compound, cDAI, cUSDC, 10**18, 0, {'from': accounts[0]})
    assert cDAI.balanceOf(accounts[0]) == 0
    assert cUSDC.balanceOf(accounts[0]) == expected


def test_exchange_underlying(accounts, registry, pool_compound, DAI, USDC):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry, 10**18, {'from': accounts[0]})
    expected = registry.get_exchange_amount(pool_compound, DAI, USDC, 10**18)

    registry.exchange(pool_compound, DAI, USDC, 10**18, 0, {'from': accounts[0]})
    assert DAI.balanceOf(accounts[0]) == 0
    assert USDC.balanceOf(accounts[0]) == expected



def test_exchange_erc20_no_return_value(accounts, registry, pool_susd, DAI, USDT):
    registry.add_pool(
        pool_susd,
        4,
        [18, 6, 6, 18, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry, 10**18, {'from': accounts[0]})

    expected = registry.get_exchange_amount(pool_susd, DAI, USDT, 10**18)
    registry.exchange(pool_susd, DAI, USDT, 10**18, 0, {'from': accounts[0]})

    assert DAI.balanceOf(accounts[0]) == 0
    assert USDT.balanceOf(accounts[0]) == expected

    USDT.approve(registry, expected, {'from': accounts[0]})
    new_expected = registry.get_exchange_amount(pool_susd, USDT, DAI, expected)
    registry.exchange(pool_susd, USDT, DAI, expected, 0, {'from': accounts[0]})

    assert DAI.balanceOf(accounts[0]) == new_expected
    assert USDT.balanceOf(accounts[0]) == 0


def test_min_dy(accounts, registry, pool_compound, DAI, USDC):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry, 10**18, {'from': accounts[0]})
    expected = registry.get_exchange_amount(pool_compound, DAI, USDC, 10**18)
    with brownie.reverts():
        registry.exchange(pool_compound, DAI, USDC, 10**18, expected + 1, {'from': accounts[0]})


def test_unknown_pool(accounts, registry, pool_compound, DAI, USDC):
    with brownie.reverts("No available market"):
        registry.exchange(pool_compound, DAI, USDC, 10**18, 0, {'from': accounts[0]})


def test_same_token(accounts, registry, pool_compound, DAI):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    with brownie.reverts("No available market"):
        registry.exchange(pool_compound, DAI, DAI, 10**18, 0, {'from': accounts[0]})


def test_same_token_underlying(accounts, registry, pool_compound, cDAI):
    registry.add_pool(
        pool_compound,
        2,
        [18, 6, 0, 0, 0, 0, 0],
        b"",
        {'from': accounts[0]}
    )

    with brownie.reverts("No available market"):
        registry.exchange(pool_compound, cDAI, cDAI, 10**18, 0, {'from': accounts[0]})


def test_token_returns_false(PoolMock, ERC20ReturnFalse, accounts, DAI, registry):
    bad_token = ERC20ReturnFalse.deploy("BAD", "Bad Token", 18, {'from': accounts[0]})
    coins = [DAI, bad_token, ZERO_ADDRESS, ZERO_ADDRESS]
    pool = PoolMock.deploy(2, coins, coins, 70, 4000000, {'from': accounts[0]})
    registry.add_pool(pool, 2, [18, 18, 0, 0, 0, 0, 0], b"", {'from': accounts[0]})

    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry, 10**18, {'from': accounts[0]})
    expected = registry.get_exchange_amount(pool, DAI, bad_token, 10**18)

    registry.exchange(pool, DAI, bad_token, 10**18, 0, {'from': accounts[0]})

    assert DAI.balanceOf(accounts[0]) == 0
    assert bad_token.balanceOf(accounts[0]) == expected

    new_expected = registry.get_exchange_amount(pool, bad_token, DAI, expected)

    bad_token.approve(registry, expected, {'from': accounts[0]})
    registry.exchange(pool, bad_token, DAI, expected, 0, {'from': accounts[0]})

    assert DAI.balanceOf(accounts[0]) == new_expected
    assert bad_token.balanceOf(accounts[0]) == 0


def test_token_returns_false_revert(PoolMock, ERC20ReturnFalse, accounts, DAI, registry):
    bad_token = ERC20ReturnFalse.deploy("BAD", "Bad Token", 18, {'from': accounts[0]})
    coins = [DAI, bad_token, ZERO_ADDRESS, ZERO_ADDRESS]
    pool = PoolMock.deploy(2, coins, coins, 70, 4000000, {'from': accounts[0]})
    registry.add_pool(pool, 2, [18, 18, 0, 0, 0, 0, 0], b"", {'from': accounts[0]})

    with brownie.reverts():
        registry.exchange(pool, bad_token, DAI, 10**18, 0, {'from': accounts[0]})
