from unittest.mock import Mock, call

from baby_steps import given, then, when
from httpx import MockTransport
from vedro import Interface

from vedro_httpx import AsyncHTTPInterface

from ._utils import (
    RouterType,
    async_http_interface,
    async_transport,
    build_url,
    request_recorder_,
    respx_mock,
)

__all__ = ("async_transport", "respx_mock", "request_recorder_",
           "async_http_interface",)  # fixtures


def test_async_interface():
    with when:
        interface = AsyncHTTPInterface()

    with then:
        assert isinstance(interface, Interface)


async def test_async_request(*, request_recorder_: Mock, async_transport: MockTransport,
                             respx_mock: RouterType):
    with given:
        base_url = build_url()
        async_http_interface = AsyncHTTPInterface(base_url=base_url,
                                                  request_recorder=request_recorder_)

        respx_mock.get("/path").respond(200)

    with when:
        async with async_http_interface._client(transport=async_transport) as client:
            response = await client.get("/path")

    with then:
        assert response.status_code == 200


async def test_async_request_recorder(*, async_http_interface: AsyncHTTPInterface,
                                      request_recorder_: Mock, async_transport: MockTransport,
                                      respx_mock: RouterType):
    with given:
        respx_mock.get("/").respond(200)

    with when:
        async with async_http_interface._client(transport=async_transport) as client:
            response = await client.get(url=build_url())

    with then:
        assert response.status_code == 200
        assert request_recorder_.mock_calls == [call.async_record(response)]
