from typing import Any, Callable, List, Optional, Tuple

import httpx
import pytest
import respx

from vedro_httpx.har import Header as HeaderType
from vedro_httpx.har import Request as RequestType
from vedro_httpx.har import Response as ResponseType
from vedro_httpx.har import SyncHARFormatter

__all__ = ("formatter", "respx_mock", "httpx_client", "build_url", "build_request",
           "build_response", "HTTPClientType", "RouterType")


HTTPClientType = Callable[..., httpx.Client]
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
def formatter() -> SyncHARFormatter:
    return SyncHARFormatter()


@pytest.fixture()
def respx_mock() -> RouterType:
    return respx.Router(assert_all_mocked=True, base_url=build_url())


@pytest.fixture()
def httpx_client(respx_mock: RouterType) -> HTTPClientType:
    mock_transport = httpx.MockTransport(respx_mock.handler)
    return lambda **kwargs: httpx.Client(transport=mock_transport, base_url=build_url(), **kwargs)
