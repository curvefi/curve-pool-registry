import brownie

def test_set_returns_none(accounts, registry_susd, pool_susd, USDT, DAI):
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry_susd, 10**18, {'from': accounts[0]})

    registry_susd.set_returns_none(USDT, False, {'from': accounts[0]})

    with brownie.reverts():
        registry_susd.exchange(pool_susd, DAI, USDT, 10**18, 0, {'from': accounts[0]})

    registry_susd.set_returns_none(USDT, True, {'from': accounts[0]})

    registry_susd.exchange(pool_susd, DAI, USDT, 10**18, 0, {'from': accounts[0]})


def test_admin_only(accounts, registry, USDT):
    with brownie.reverts("dev: admin-only function"):
        registry.set_returns_none(USDT, False, {'from': accounts[1]})
