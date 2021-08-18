# @version 0.2.15
"""
@title Curve Gauge Registry
@license MIT
"""


interface Factory:
    def gauge_implementation() -> address: view


PROXY_PRE_BYTECODE: constant(Bytes[15]) = 0x366000600037611000600036600073
PROXY_POST_BYTECODE: constant(Bytes[16]) = 0x5AF4602C57600080FD5B6110006000F3


owner: public(address)
factory: public(address)
chain_id: public(uint256)

gauge_count: public(uint256)
gauge_list: public(address[MAX_UINT256])
# [pool_address 20 bytes][version 12 bytes]
gauge_data: HashMap[address, uint256]


@external
def __init__(_factory: address):
    self.owner = msg.sender
    self.chain_id = chain.id


@pure
@internal
def _get_proxy_codehash(_impl_addr: Bytes[20]) -> bytes32:
    return keccak256(concat(PROXY_PRE_BYTECODE, _impl_addr, PROXY_POST_BYTECODE))


@external
def register(_gauge: address, _pool: address, _version: uint256):
    impl_addr: Bytes[20] = slice(
        convert(Factory(self.factory).gauge_implementation(), bytes32), 12, 20
    )
    assert msg.sender.codehash == self._get_proxy_codehash(impl_addr) or msg.sender == self.owner

    index: uint256 = self.gauge_count
    self.gauge_list[index] = _gauge
    self.gauge_count = index + 1

    self.gauge_data[_gauge] = shift(convert(_pool, uint256), 96) + _version


@view
@external
def pool_address(_gauge: address) -> address:
    return convert(shift(self.gauge_data[_gauge], 96), address)


@view
@external
def gauge_version(_gauge: address) -> uint256:
    return self.gauge_data[_gauge] % 2 ** 96
