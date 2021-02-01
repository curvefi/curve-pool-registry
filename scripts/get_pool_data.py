import json
from pathlib import Path

import requests

GITHUB_POOLS = "https://api.github.com/repos/curvefi/curve-contract/contents/contracts/pools"
GITHUB_POOLDATA = "https://raw.githubusercontent.com/curvefi/curve-contract/master/contracts/pools/{}/pooldata.json"  # noqa: E501


def get_pool_data(force_fetch: bool = False) -> dict:
    """
    Fetch data about existing Curve pools from Github.

    Pool Data is pulled from `curve-contract/contacts/pools/[POOL_NAME]/pooldata.json`
    and stored at `./pooldata.json`. This JSON is then used for adding new pools to the registry
    and for forked-mainnet testing.

    To update the pools, delete `pooldata.json` or use `brownie run get_pool_data`
    """
    path = Path(__file__).parent.parent.joinpath("pooldata.json")

    if not force_fetch and path.exists():
        try:
            with path.open() as fp:
                return json.load(fp)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    print("Querying Github for pool deployments...")
    pool_data = {}
    pool_names = [i["name"] for i in requests.get(GITHUB_POOLS).json() if i["type"] == "dir"]

    for name in pool_names:
        data = requests.get(GITHUB_POOLDATA.format(name)).json()
        if "swap_address" not in data:
            print(f"Cannot add {name} - no deployment address!")
            continue
        pool_data[name] = data

    with path.open("w") as fp:
        json.dump(pool_data, fp, sort_keys=True, indent=2)

    print(f"Pool deployment data saved at {path.as_posix()}")
    return pool_data


def main():
    return get_pool_data(True)
