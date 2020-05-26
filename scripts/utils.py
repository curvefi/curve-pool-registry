from typing import List


def pack_values(values: List[int]) -> bytes:
    """
    Tightly pack integer values as a `bytes32` value prior to calling `Registry.add_pool`

    Arguments
    ---------
    values : list
        List of integer values to pack.

    Returns
    -------
    bytes
        32 byte big-endian bytestring of tightly packed values.
    """

    packed = b"".join(i.to_bytes(1, "big") for i in values)
    padded = packed + bytes(32 - len(values))
    return padded
