ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_get_decimals_lending(
    alice,
    registry,
    lending_swap,
    lp_token,
    n_coins,
    is_v1,
    rate_method_id,
    underlying_decimals,
    wrapped_decimals,
):
    registry.add_pool(
        lending_swap,
        n_coins,
        lp_token,
        rate_method_id,
        0,
        0,
        hasattr(lending_swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )
    zero_pad = [0] * (8 - n_coins)

    assert registry.get_decimals(lending_swap) == wrapped_decimals + zero_pad
    assert registry.get_underlying_decimals(lending_swap) == underlying_decimals + zero_pad


def test_get_decimals(alice, registry, swap, lp_token, n_coins, is_v1, underlying_decimals):
    registry.add_pool_without_underlying(
        swap,
        n_coins,
        lp_token,
        "0x00",
        0,
        0,  # use rates
        hasattr(swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )

    assert registry.get_decimals(swap) == underlying_decimals + [0] * (8 - n_coins)


def test_get_decimals_metapool(
    alice,
    registry,
    swap,
    meta_swap,
    lp_token,
    meta_lp_token,
    n_coins,
    n_metacoins,
    is_v1,
    meta_decimals,
    underlying_decimals,
):
    registry.add_pool_without_underlying(
        swap,
        n_coins,
        lp_token,
        "0x00",
        0,
        0,  # use rates
        hasattr(swap, "initial_A"),
        is_v1,
        "",
        {"from": alice},
    )
    registry.add_metapool(meta_swap, n_metacoins, meta_lp_token, 0, "", {"from": alice})

    expected = meta_decimals[:-1] + underlying_decimals
    expected += [0] * (8 - len(expected))

    assert registry.get_decimals(meta_swap) == meta_decimals + [0] * (8 - n_metacoins)
    assert registry.get_underlying_decimals(meta_swap) == expected
