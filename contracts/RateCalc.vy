# @version 0.2.11
"""
@title Curve Coin Rate Calculator
@license MIT
@author Curve.Fi
"""


@view
@external
def get_rate(_coin: address, _rate_method_id: Bytes[4]) -> uint256:
    """
    @notice Calculate the swap rate between a coin and it's underlying
        asset.
    @param _coin The coin address
    @param _rate_method_id The function selector in `_coin` contract
        for querying the swap rate
    @return The swap rate between `_coin` and it's underlying asset
    """
    result: uint256 = convert(
        raw_call(_coin, _rate_method_id, max_outsize=32, is_static_call=True), uint256
    )
    if _rate_method_id == method_id("ratio()"):  # ankrETH
        result = 10 ** 36 / result
    return result
