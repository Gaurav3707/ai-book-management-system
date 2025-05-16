import pytest
from test_user import access_token

@pytest.fixture(scope="session")
def ensure_access_token():
    assert access_token is not None, "Access token is not initialized. Ensure test_user runs first."
