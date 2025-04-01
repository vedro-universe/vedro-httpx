from baby_steps import given, then, when

from tests._utils import (
    HTTPClientType,
    RouterType,
    build_response,
    builder,
    respx_mock,
    sync_formatter,
    sync_httpx_client,
    sync_transport,
)
from vedro_httpx.recorder import SyncHARFormatter

__all__ = ("sync_formatter", "sync_httpx_client", "sync_transport", "builder",
           "respx_mock",)  # fixtures


def test_response(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                  sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response()


def test_response_version(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                          sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, http_version="HTTP/2")
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(httpVersion="HTTP/2")


def test_response_with_status(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                              sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(404)
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(status=404, statusText="Not Found")


def test_response_with_headers(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                               sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, headers=[
            ("x-header", "value1"),
            ("x-header", "value2")
        ])
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(headers=[
            {"name": "x-header", "value": "value1"},
            {"name": "x-header", "value": "value2"}
        ])


def test_response_with_redirect(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(301, headers=[
            ("location", "/redirected")
        ])
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            status=301,
            statusText="Moved Permanently",
            headers=[
                {"name": "location", "value": "/redirected"}
            ],
            redirectURL="/redirected"
        )


def test_response_with_cookies(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                               sync_httpx_client: HTTPClientType):
    with given:
        cookie_attrs = ("Domain=localhost; expires=Sat, 01-Jan-2024 00:00:00 GMT; HttpOnly; "
                        "Max-Age=3600; Path=/; SameSite=Strict; Secure; Version=1")

        respx_mock.get("/").respond(200, headers=[
            ("set-cookie", "name1=value1"),
            ("set-cookie", f"name2=value2; {cookie_attrs}"),
        ])
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            headers=[
                {"name": "set-cookie", "value": "name1=value1"},
                {"name": "set-cookie", "value": f"name2=value2; {cookie_attrs}"}
            ],
            cookies=[
                {
                    "name": "name1",
                    "value": "value1"
                },
                {
                    "name": "name2",
                    "value": "value2",
                    "path": "/",
                    "domain": "localhost",
                    "expires": "2024-01-01T00:00:00+00:00",
                    "httpOnly": True,
                    "secure": True,
                }
            ]
        )


def test_response_with_text_content(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                    sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, text="text")
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            headers=[
                {"name": "content-length", "value": "4"},
                {"name": "content-type", "value": "text/plain; charset=utf-8"},
            ],
            content={
                "size": 4,
                "mimeType": "text/plain; charset=utf-8",
                "text": "text"
            }
        )


def test_response_with_json_content(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                    sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, json={"key": "value"})
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            headers=[
                {"name": "content-length", "value": "15"},
                {"name": "content-type", "value": "application/json"},
            ],
            content={
                "size": 15,
                "mimeType": "application/json",
                "text": '{"key":"value"}'
            }
        )


def test_response_with_binary_content(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                      sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, content=b"binary")
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            headers=[
                {"name": "content-length", "value": "6"},
            ],
            content={
                "size": 6,
                "mimeType": "x-unknown",
                "encoding": "base64",
                "text": "YmluYXJ5"
            }
        )


def test_response_with_octet_stream_content(*, sync_formatter: SyncHARFormatter,
                                            respx_mock: RouterType,
                                            sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, content=b"binary",
                                    content_type="application/octet-stream")
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            headers=[
                {"name": "content-length", "value": "6"},
                {"name": "content-type", "value": "application/octet-stream"},
            ],
            content={
                "size": 6,
                "mimeType": "application/octet-stream",
                "encoding": "base64",
                "text": "YmluYXJ5"
            }
        )


def test_stream_response(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                         sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, content=b"binary")
        with sync_httpx_client() as client:
            with client.stream("GET", "/") as response:
                # Manipulating `response._content` directly is a workaround due to respx's
                # limitations in simulating streaming behavior
                delattr(response, "_content")
                response.is_stream_consumed = True

    with when:
        result = sync_formatter.format_response(response)

    with then:
        assert result == build_response(
            headers=[
                {"name": "content-length", "value": "6"},
            ],
            content={
                "size": 0,
                "mimeType": "x-unknown",
                "text": "(stream)",
                "comment": "Stream consumed"
            }
        )
