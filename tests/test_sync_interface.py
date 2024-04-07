from unittest.mock import Mock, call

from baby_steps import given, then, when
from httpx import MockTransport
from vedro import Interface

from vedro_httpx import SyncHTTPInterface

from ._utils import (
    RouterType,
    build_url,
    request_recorder_,
    respx_mock,
    sync_http_interface,
    sync_transport,
)

__all__ = ("sync_transport", "respx_mock", "request_recorder_", "sync_http_interface",)  # fixtures


def test_sync_interface():
    with when:
        interface = SyncHTTPInterface()

    with then:
        assert isinstance(interface, Interface)


def test_sync_request(*, request_recorder_: Mock, sync_transport: MockTransport,
                      respx_mock: RouterType):
    with given:
        base_url = build_url()
        sync_http_interface = SyncHTTPInterface(base_url=base_url,
                                                request_recorder=request_recorder_)

        respx_mock.get("/path").respond(200)

    with when:
        with sync_http_interface._client(transport=sync_transport) as client:
            response = client.get("/path")

    with then:
        assert response.status_code == 200


def test_sync_request_recorder(*, sync_http_interface: SyncHTTPInterface, request_recorder_: Mock,
                               sync_transport: MockTransport, respx_mock: RouterType):
    with given:
        respx_mock.get("/").respond(200)

    with when:
        with sync_http_interface._client(transport=sync_transport) as client:
            response = client.get(url=build_url())

    with then:
        assert response.status_code == 200
        assert request_recorder_.mock_calls == [call.sync_record(response)]
