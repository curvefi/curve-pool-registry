# @version 0.2.15
"""
@title Curve Gauge Registry
@license MIT
"""


interface AddressProvider:
    def admin() -> address: view
    def get_address(_id: uint256) -> address: view

interface Factory:
    def gauge_implementation() -> address: view


ADDR_PROVIDER: constant(address) = 0x0000000022D53366457F9d5E68Ec105046FC4383
# See: https://eips.ethereum.org/EIPS/eip-1167
PROXY_PRE_BYTECODE: constant(Bytes[10]) = 0x363d3d373d3d3d363d73
PROXY_POST_BYTECODE: constant(Bytes[15]) = 0x5af43d82803e903d91602b57fd5bf3


factory: public(address)
chain_id: public(uint256)

gauge_count: public(uint256)
gauge_list: public(address[MAX_INT128])
# [pool_address 20 bytes][version 12 bytes]
gauge_data: HashMap[address, uint256]


@external
def __init__():
    self.chain_id = chain.id
    self.factory = AddressProvider(ADDR_PROVIDER).get_address(3)  # metapool factory


@external
def register(_gauge: address, _pool: address, _version: uint256):
    proxy_codehash: bytes32 = keccak256(
        concat(
            PROXY_PRE_BYTECODE,
            slice(convert(Factory(self.factory).gauge_implementation(), bytes32), 12, 20),
            PROXY_POST_BYTECODE,
        )
    )
    assert (
        msg.sender.codehash == proxy_codehash
        or msg.sender == AddressProvider(ADDR_PROVIDER).admin()
    )

    index: uint256 = self.gauge_count
    self.gauge_list[index] = _gauge
    self.gauge_count = index + 1

    self.gauge_data[_gauge] = shift(convert(_pool, uint256), 96) + _version


@view
@external
def pool_address(_gauge: address) -> address:
    return convert(shift(self.gauge_data[_gauge], -96), address)


@view
@external
def gauge_version(_gauge: address) -> uint256:
    return self.gauge_data[_gauge] % 2 ** 96


@external
def cache_factory():
    self.factory = AddressProvider(ADDR_PROVIDER).get_address(3)
