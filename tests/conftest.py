from pathlib import Path

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_collection(session):
    yield

    base_path = Path(session.startdir)
    paths = set(Path(i.fspath).relative_to(base_path).parts[1] for i in session.items)

    if "forked" in paths and "local" in paths:
        raise pytest.UsageError(
            "Cannot run local and forked tests at the same time. Use `brownie test tests/fork`"
            " or `brownie test tests/local`"
        )


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# account helpers


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]
