# @version 0.2.11
"""
@title Mock Curve Pool Rate Calculator
"""


@view
@external
def get_rate(_coin: address) -> uint256:
    result: Bytes[32] = raw_call(_coin, 0x71ca337d, max_outsize=32, is_static_call=True)
    return 10 ** 36 / convert(result, uint256)
