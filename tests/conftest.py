import pytest


@pytest.fixture(scope="session")
def file_start() -> str:
    """The start of any link to the sepal platform.

    Args:
        the value of the sandbox path
    """
    return "https://sepal.io/api/sandbox/jupyter/files/"
