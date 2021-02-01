from typing import List


def pack_values(values: List[int]) -> bytes:
    """
    Tightly pack integer values.

    Each number is represented as a single byte within a low-endian bytestring. The
    bytestring is then converted back to a `uint256` to be used in `Registry.add_pool`

    Arguments
    ---------
    values : list
        List of integer values to pack

    Returns
    -------
    int
        32 byte little-endian bytestring of packed values, converted to an integer
    """
    assert max(values) < 256

    return sum(i << c * 8 for c, i in enumerate(values))
