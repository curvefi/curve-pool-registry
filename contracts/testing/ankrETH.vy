# @version 0.2.8
"""
@notice Mock ankrETH contract for testing registry rate getter
"""


ratio: public(uint256)


@external
def __init__():
    self.ratio = 10 ** 18


@external
def update_ratio(new_ratio: uint256):
    assert new_ratio < self.ratio
    self.ratio = new_ratio
