import brownie


def test_admin_only(registry, accounts, DAI):
    with brownie.reverts("dev: admin-only function"):
        registry.claim_token_balance(DAI, {'from': accounts[1]})


def test_claim_normal(registry, accounts, DAI):
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.transfer(registry, 10**18, {'from': accounts[0]})
    registry.claim_token_balance(DAI, {'from': accounts[0]})

    assert DAI.balanceOf(registry) == 0
    assert DAI.balanceOf(accounts[0]) == 10**18


def test_claim_no_return(registry, accounts, USDT):
    USDT._mint_for_testing(10**18, {'from': accounts[0]})
    USDT.transfer(registry, 10**18, {'from': accounts[0]})
    registry.claim_token_balance(USDT, {'from': accounts[0]})

    assert USDT.balanceOf(registry) == 0
    assert USDT.balanceOf(accounts[0]) == 10**18


def test_claim_return_false(registry, accounts, BAD):
    BAD._mint_for_testing(10**18, {'from': accounts[0]})
    BAD.transfer(registry, 10**18, {'from': accounts[0]})
    registry.claim_token_balance(BAD, {'from': accounts[0]})

    assert BAD.balanceOf(registry) == 0
    assert BAD.balanceOf(accounts[0]) == 10**18
