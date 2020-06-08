import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

def test_exchange_to_eth(accounts, registry_eth, pool_eth, yDAI):
    yDAI._mint_for_testing(10**18, {'from': accounts[0]})
    yDAI.approve(registry_eth, 10**18, {'from': accounts[0]})
    balance = accounts[0].balance()
    expected = registry_eth.get_exchange_amount(pool_eth, yDAI, ETH_ADDRESS, 10**18)

    registry_eth.exchange(pool_eth, yDAI, ETH_ADDRESS, 10**18, 0, {'from': accounts[0]})
    assert yDAI.balanceOf(accounts[0]) == 0
    assert accounts[0].balance() == balance + expected


def test_exchange_from_eth(accounts, registry_eth, pool_eth, yDAI):
    expected = registry_eth.get_exchange_amount(pool_eth, ETH_ADDRESS, yDAI, 10**18)

    registry_eth.exchange(pool_eth, ETH_ADDRESS, yDAI, 10**18, 0, {'from': accounts[0], 'value': 10**18})
    assert yDAI.balanceOf(accounts[0]) == expected


def test_exchange_to_eth_underlying(accounts, registry_eth, pool_eth, DAI):
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry_eth, 10**18, {'from': accounts[0]})
    balance = accounts[0].balance()
    expected = registry_eth.get_exchange_amount(pool_eth, DAI, ETH_ADDRESS, 10**18)

    registry_eth.exchange(pool_eth, DAI, ETH_ADDRESS, 10**18, 0, {'from': accounts[0]})
    assert DAI.balanceOf(accounts[0]) == 0
    assert accounts[0].balance() == balance + expected


def test_exchange_from_eth_underlying(accounts, registry_eth, pool_eth, DAI):
    expected = registry_eth.get_exchange_amount(pool_eth, ETH_ADDRESS, DAI, 10**18)

    registry_eth.exchange(pool_eth, ETH_ADDRESS, DAI, 10**18, 0, {'from': accounts[0], 'value': 10**18})
    assert DAI.balanceOf(accounts[0]) == expected



def test_from_eth_wrong_value(accounts, registry_eth, pool_eth, yDAI):
    yDAI._mint_for_testing(10**18, {'from': accounts[0]})
    yDAI.approve(registry_eth, 10**18, {'from': accounts[0]})
    balance = accounts[0].balance()
    expected = registry_eth.get_exchange_amount(pool_eth, yDAI, ETH_ADDRESS, 10**18)

    registry_eth.exchange(pool_eth, yDAI, ETH_ADDRESS, 10**18, 0, {'from': accounts[0]})
    assert yDAI.balanceOf(accounts[0]) == 0
    assert accounts[0].balance() == balance + expected


def test_msg_value_too_low(accounts, registry_eth, pool_eth, yDAI):
    with brownie.reverts("Incorrect ETH amount"):
        registry_eth.exchange(pool_eth, ETH_ADDRESS, yDAI, 10**18, 0, {'from': accounts[0], 'value': 31337})



def test_msg_value_too_high(accounts, registry_eth, pool_eth, yDAI):
    with brownie.reverts("Incorrect ETH amount"):
        registry_eth.exchange(pool_eth, ETH_ADDRESS, yDAI, 10**18, 0, {'from': accounts[0], 'value': 10**19})


def test_no_ether_sent(accounts, registry_eth, pool_eth, yDAI):
    with brownie.reverts("Incorrect ETH amount"):
        registry_eth.exchange(pool_eth, ETH_ADDRESS, yDAI, 10**18, 0, {'from': accounts[0]})


def test_ether_with_token_exchange(accounts, registry_eth, pool_eth, yDAI, yUSDT):
    yDAI._mint_for_testing(10**18, {'from': accounts[0]})
    yDAI.approve(registry_eth, 10**18, {'from': accounts[0]})
    with brownie.reverts():
        registry_eth.exchange(pool_eth, yDAI, yUSDT, 10**18, 0, {'from': accounts[0], 'value': "1 ether"})


def test_ether_with_underlying_token_exchange(accounts, registry_eth, pool_eth, DAI, USDT):
    DAI._mint_for_testing(10**18, {'from': accounts[0]})
    DAI.approve(registry_eth, 10**18, {'from': accounts[0]})
    with brownie.reverts():
        registry_eth.exchange(pool_eth, DAI, USDT, 10**18, 0, {'from': accounts[0], 'value': "1 ether"})
