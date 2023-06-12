from baby_steps import given, then, when
from vedro import Interface

from vedro_httpx import SyncHTTPInterface
from vedro_httpx._sync_http_interface import SyncClient


def test_sync_interface():
    with when:
        interface = SyncHTTPInterface()

    with then:
        assert isinstance(interface, Interface)


def test_sync_client():
    with given:
        interface = SyncHTTPInterface()

    with when:
        client = interface._client()

    with then:
        assert isinstance(client, SyncClient)
