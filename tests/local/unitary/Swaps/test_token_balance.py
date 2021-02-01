import brownie


def test_admin_only(registry_swap, bob, lp_token):
    with brownie.reverts("dev: admin-only function"):
        registry_swap.claim_balance(lp_token, {"from": bob})


def test_claim_normal(registry_swap, alice, lp_token):
    lp_token._mint_for_testing(registry_swap, 10 ** 18, {"from": alice})
    registry_swap.claim_balance(lp_token, {"from": alice})

    assert lp_token.balanceOf(registry_swap) == 0
    assert lp_token.balanceOf(alice) == 10 ** 18


def test_claim_no_return(registry_swap, alice, ERC20NoReturn):
    token = ERC20NoReturn.deploy("Test", "TST", 18, {"from": alice})
    token._mint_for_testing(registry_swap, 10 ** 18, {"from": alice})
    registry_swap.claim_balance(token, {"from": alice})

    assert token.balanceOf(registry_swap) == 0
    assert token.balanceOf(alice) == 10 ** 18


def test_claim_return_false(registry_swap, alice, ERC20ReturnFalse):
    token = ERC20ReturnFalse.deploy("Test", "TST", 18, {"from": alice})
    token._mint_for_testing(registry_swap, 10 ** 18, {"from": alice})
    registry_swap.claim_balance(token, {"from": alice})

    assert token.balanceOf(registry_swap) == 0
    assert token.balanceOf(alice) == 10 ** 18


def test_claim_ether(registry_swap, alice, bob):
    bob.transfer(registry_swap, "1 ether")
    balance = alice.balance()

    registry_swap.claim_balance("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", {"from": alice})
    assert alice.balance() == balance + "1 ether"
