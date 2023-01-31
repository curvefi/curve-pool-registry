from brownie import accounts, AddressProvider, CryptoRegistry


dev = accounts.load("dev")  # 0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a


def main():
    provider = AddressProvider.at("0x0000000022D53366457F9d5E68Ec105046FC4383")
    # transfer to proxy so 0xbabe can manage
    provider.commit_transfer_ownership("0x6f8EEF407B974DFF82c53FF939CC1EBb699383fB", {"from": dev})
    # add pool to crypto registry
    registry = CryptoRegistry.at("0x8A4694401bE8F8FCCbC542a3219aF1591f87CE17")
    registry.add_pool(
        "0x056C6C5e684CeC248635eD86033378Cc444459B0",  # pool
        "0x0CA1C1eC4EBf3CC67a9f545fF90a3795b318cA4a",  # lp
        "0xd91770E868c7471a9585d1819143063A40c54D00",  # gauge
        "0xE3FFF29d4DC930EBb787FeCd49Ee5963DADf60b6",  # zap
        2,  # number of coins
        "Curve.fi EURe/USD",  # pool name
        "0x7f90122BF0700F9E7e1F688fe926940E8839F353",  # base pool
        False,  # is rebasing?
        {"from": dev},
    )
    