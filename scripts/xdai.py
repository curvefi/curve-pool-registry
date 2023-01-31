from brownie import accounts, AddressProvider, CryptoRegistry


dev = accounts.at("0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", force=True)

def pack_values(values):
    assert max(values) < 256

    return sum(i << c * 8 for c, i in enumerate(values))


def main():
    provider = AddressProvider.at("0x0000000022D53366457F9d5E68Ec105046FC4383")
    # transfer to proxy so 0xbabe can manage
    provider.commit_transfer_ownership("0x6f8EEF407B974DFF82c53FF939CC1EBb699383fB", {"from": dev})
    # add pool to crypto registry
    registry = CryptoRegistry.at("0x8A4694401bE8F8FCCbC542a3219aF1591f87CE17")
    registry.add_pool(
        "0x056C6C5e684CeC248635eD86033378Cc444459B0",  # pool
        2,
        "0x0CA1C1eC4EBf3CC67a9f545fF90a3795b318cA4a",  # lp
        pack_values([18, 18]),
        "Curve.fi EURe/USD",  # pool name
        {"from": dev},
    )
    