# curve-pool-registry

* add a pool (admin) or maybe remove (blacklist) a pool
* enumerate pools
* check which pools are available to exchange addr1->addr2
* check which coins a pool has (and how many)
* exchange (plain or non-plain coins)
* get_dy (how much coins you get in exchange for dx) for a pair
* functions for deposit / withdraw - but the contract only deposits compounding tokens and it's an external contract `deposit.vy` which wraps/unwraps them (if compounding are used). Maybe a registry could abstract that away, too

## Existing pools
See [`curvefi/curve-contract/deployed/`](https://github.com/curvefi/curve-contract/tree/master/deployed)

* [`pool_compound`](https://github.com/curvefi/curve-contract/blob/pool_compound/vyper/stableswap.vy)
* [`pool_y`](https://github.com/curvefi/curve-contract/blob/pool_y/vyper/stableswap.vy)
* [`pool_susd_plain`](https://github.com/curvefi/curve-contract/blob/pool_susd_plain/vyper/stableswap.vy)
* [`pool_usdt`](https://github.com/curvefi/curve-contract/blob/pool_usdt/vyper/stableswap.vy)
* [`pool_busd`](https://github.com/curvefi/curve-contract/blob/pool_busd/vyper/stableswap.vy)
* [`pool_pax`](https://github.com/curvefi/curve-contract/blob/pool_pax/vyper/stableswap.vy)
