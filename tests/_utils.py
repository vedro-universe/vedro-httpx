from typing import Any, Callable, List, Optional, Tuple
from unittest.mock import Mock

import httpx
import pytest
import respx
from httpx import MockTransport

from vedro_httpx import AsyncHTTPInterface, RequestRecorder, SyncHTTPInterface
from vedro_httpx.har import AsyncHARFormatter, HARBuilder
from vedro_httpx.har import Header as HeaderType
from vedro_httpx.har import Request as RequestType
from vedro_httpx.har import Response as ResponseType
from vedro_httpx.har import SyncHARFormatter

__all__ = ("sync_formatter", "async_formatter", "sync_httpx_client", "async_httpx_client",
           "sync_transport", "async_transport", "builder", "respx_mock", "build_url",
           "build_request", "build_response", "get_request_multipart", "request_recorder",
           "request_recorder_", "sync_http_interface", "async_http_interface",
           "HTTPClientType", "AsyncHTTPClientType", "RouterType",)


HTTPClientType = Callable[..., httpx.Client]
AsyncHTTPClientType = Callable[..., httpx.AsyncClient]
RouterType = respx.Router


def build_url(path: str = "/", params: Optional[httpx.QueryParams] = None, *,
              base_url: str = "http://localhost") -> str:
    url = f"{base_url}{path}"
    if params:
        url += f"?{params}"
    return url


def build_request(headers: Optional[List[HeaderType]] = None, **kwargs: Any) -> RequestType:
    headers_ = [
        {"name": "host", "value": "localhost"},
        {"name": "accept", "value": "*/*"},
        {"name": "accept-encoding", "value": "gzip, deflate"},
        {"name": "connection", "value": "keep-alive"},
        {"name": "user-agent", "value": f"python-httpx/{httpx.__version__}"}
    ]
    if headers:
        headers_ += headers

    return {
        "method": "GET",
        "url": build_url(),
        "httpVersion": "HTTP/1.1",
        "cookies": [],
        "headers": headers_,
        "queryString": [],
        "headersSize": -1,
        "bodySize": -1,
        **kwargs
    }


def build_response(headers: Optional[List[HeaderType]] = None, **kwargs: Any) -> ResponseType:
    headers_ = []
    if headers:
        headers_ += headers

    return {
        "status": 200,
        "statusText": "OK",
        "httpVersion": "HTTP/1.1",
        "cookies": [],
        "headers": headers_,
        "content": {
            "size": 0,
            "mimeType": "x-unknown",
        },
        "redirectURL": "",
        "headersSize": -1,
        "bodySize": -1,
        **kwargs
    }


def get_request_multipart(request: httpx.Request,
                          file_content: Optional[bytes] = None) -> Tuple[str, str]:
    boundary = request.headers["content-type"].split("boundary=")[1]
    payload = request.content.decode()
    if file_content:
        payload = payload.replace(file_content.decode(), "(binary)")
    return boundary, payload


@pytest.fixture
def builder() -> HARBuilder:
    from vedro_httpx import __version__ as version
    return HARBuilder("vedro-httpx", version)


@pytest.fixture
def sync_formatter(builder: HARBuilder) -> SyncHARFormatter:
    return SyncHARFormatter(builder)


@pytest.fixture
def async_formatter(builder: HARBuilder) -> AsyncHARFormatter:
    return AsyncHARFormatter(builder)


@pytest.fixture()
def respx_mock() -> RouterType:
    return respx.Router(assert_all_mocked=True, base_url=build_url())


@pytest.fixture()
def sync_transport(respx_mock: RouterType) -> MockTransport:
    return MockTransport(respx_mock.handler)


@pytest.fixture()
def sync_httpx_client(sync_transport: MockTransport) -> HTTPClientType:
    return lambda **kwargs: httpx.Client(transport=sync_transport, base_url=build_url(), **kwargs)


@pytest.fixture()
def async_transport(respx_mock: RouterType) -> MockTransport:
    return MockTransport(respx_mock.async_handler)


@pytest.fixture()
def async_httpx_client(async_transport: MockTransport) -> AsyncHTTPClientType:
    return lambda **kwargs: httpx.AsyncClient(transport=async_transport,
                                              base_url=build_url(), **kwargs)


@pytest.fixture
def request_recorder(builder: HARBuilder, sync_formatter: SyncHARFormatter,
                     async_formatter: AsyncHARFormatter) -> RequestRecorder:
    return RequestRecorder(builder, sync_formatter, async_formatter)


@pytest.fixture
def request_recorder_() -> Mock:
    return Mock(spec=RequestRecorder)


@pytest.fixture
def sync_http_interface(request_recorder_: RequestRecorder) -> SyncHTTPInterface:
    return SyncHTTPInterface(request_recorder=request_recorder_)


@pytest.fixture
def async_http_interface(request_recorder_: RequestRecorder) -> AsyncHTTPInterface:
    return AsyncHTTPInterface(request_recorder=request_recorder_)
