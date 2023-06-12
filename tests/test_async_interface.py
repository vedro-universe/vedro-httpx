from baby_steps import given, then, when
from vedro import Interface

from vedro_httpx import AsyncHTTPInterface
from vedro_httpx._async_http_interface import AsyncClient


def test_async_interface():
    with when:
        interface = AsyncHTTPInterface()

    with then:
        assert isinstance(interface, Interface)


def test_async_client():
    with given:
        interface = AsyncHTTPInterface()

    with when:
        client = interface._client()

    with then:
        assert isinstance(client, AsyncClient)
