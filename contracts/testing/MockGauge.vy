# @version 0.2.15


ADDR_PROVIDER: constant(address) = 0x0000000022D53366457F9D5E68EC105046FC4383
ETH_ADDR: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE


interface AddressProvider:
    def get_address(_id: uint256) -> address: view

interface GaugeRegistry:
    def register(_gauge: address, _pool: address, _version: uint256): nonpayable


def initialize():
    gauge_registry: address = AddressProvider(ADDR_PROVIDER).get_address(5)
    GaugeRegistry(gauge_registry).register(self, ETH_ADDR, 1)
