import pytest
from baby_steps import given, then, when

from vedro_httpx.spec_generator._utils import humanize_identifier


@pytest.mark.parametrize(("name", "expected"), [
    ("", ""),
    ("client id", "Client id"),
    ("client_id", "Client id"),
    ("_client_id_", "Client id"),
    ("clientId", "Client id"),
    ("ClientName", "Client name"),
    ("clientHTTPStatus", "Client http status"),
    ("HTTPResponse", "Http response"),
    ("StatusOK", "Status ok"),
    ("version2Name", "Version2 name"),
    ("CLIENT_ID", "Client id"),
    ("singleA", "Single a"),
    ("X-Client-ID", "X client id"),
])
def test_humanize_identifier(name: str, expected: str):
    with given:
        name = name

    with when:
        result = humanize_identifier(name)

    with then:
        assert result == expected
