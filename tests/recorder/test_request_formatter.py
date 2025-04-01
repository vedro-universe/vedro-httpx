import httpx
import pytest
from baby_steps import given, then, when

from tests._utils import (
    HTTPClientType,
    RouterType,
    build_request,
    build_url,
    builder,
    get_request_multipart,
    respx_mock,
    sync_formatter,
    sync_httpx_client,
    sync_transport,
)
from vedro_httpx.recorder import SyncHARFormatter

__all__ = ("sync_formatter", "sync_httpx_client", "sync_transport", "builder",
           "respx_mock",)  # fixtures


def test_get_request(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                     sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with sync_httpx_client() as client:
            response = client.get("/")

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request()


@pytest.mark.parametrize("path", ["/users", "/users#fragment"])
def test_get_request_with_path(path: str, *, sync_formatter: SyncHARFormatter,
                               respx_mock: RouterType, sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/users").respond(200)
        with sync_httpx_client() as client:
            response = client.get(path)

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(url=build_url("/users"))


def test_get_request_with_params(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                 sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with sync_httpx_client() as client:
            params = httpx.QueryParams([("id", 1), ("id", 2)])
            response = client.get("/", params=params)

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(
            url=build_url("/", params=params),
            queryString=[
                {"name": "id", "value": "1"},
                {"name": "id", "value": "2"}
            ]
        )


def test_get_request_with_headers(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                  sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with sync_httpx_client() as client:
            headers = httpx.Headers([("x-header", "value1"), ("x-header", "value2")])
            response = client.get("/", headers=headers)

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(headers=[
            {"name": "x-header", "value": "value1"},
            {"name": "x-header", "value": "value2"}
        ])


def test_get_request_with_cookies(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                  sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)

        cookies = httpx.Cookies({"cookie1": "value1", "cookie2": "value2"})
        with sync_httpx_client(cookies=cookies) as client:
            # Setting per-request cookies=<...> is being deprecated,
            # because the expected behaviour on cookie persistence is ambiguous
            response = client.get("/")

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(
            cookies=[
                {"name": "cookie1", "value": "value1"},
                {"name": "cookie2", "value": "value2"}
            ],
            headers=[
                {"name": "cookie", "value": "cookie1=value1; cookie2=value2"}
            ])


def test_post_request_no_data(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                              sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            response = client.post("/")

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        expected_result = build_request(method="POST")
        expected_result["headers"].insert(1, {"name": "content-length", "value": "0"})

        assert result == expected_result


def test_post_request_json_data(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            response = client.post("/", json={"id": 1, "name": "User"})

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "22"},
                {"name": "content-type", "value": "application/json"},
            ],
            postData={
                "mimeType": "application/json",
                "text": '{"id":1,"name":"User"}'
            }
        )


def test_post_request_binary_data(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                  sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            response = client.post("/", content=b"binary", headers={
                "content-type": "application/octet-stream"
            })

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-type", "value": "application/octet-stream"},
                {"name": "content-length", "value": "6"},
            ],
            postData={
                "mimeType": "application/octet-stream",
                "text": "binary"
            }
        )


def test_post_request_form_data(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            response = client.post("/", data={"id": "1", "name": "User"})

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "14"},
                {"name": "content-type", "value": "application/x-www-form-urlencoded"},
            ],
            postData={
                "mimeType": "application/x-www-form-urlencoded",
                "text": "id=1&name=User",
                "params": [
                    {"name": "id", "value": "1"},
                    {"name": "name", "value": "User"}
                ]
            }
        )


def test_post_request_multipart_data(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                     sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            # httpx does not support constructing multipart requests with form data without files
            boundary = "boundary"
            content = "\r\n".join([
                f"--{boundary}",
                'Content-Disposition: form-data; name="id"',
                "",
                "1",
                f"--{boundary}",
                'Content-Disposition: form-data; name="name"',
                "",
                "User",
                f"--{boundary}--",
                ""
            ])
            response = client.post("/", content=content, headers={
                "content-type": f"multipart/form-data; boundary={boundary}"
            })

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-type", "value": f"multipart/form-data; boundary={boundary}"},
                {"name": "content-length", "value": "139"},
            ],
            postData={
                "mimeType": f"multipart/form-data; boundary={boundary}",
                "params": [
                    {"name": "id", "value": "1"},
                    {"name": "name", "value": "User"}
                ],
                "text": content,
            }
        )


def test_post_request_multipart_files(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                                      sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            file_name, file_content = "file.txt", b"file content"
            response = client.post("/", files={"file": (file_name, file_content)})

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        boundary, content = get_request_multipart(response.request, file_content)
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "182"},
                {"name": "content-type", "value": f"multipart/form-data; boundary={boundary}"},
            ],
            postData={
                "mimeType": f"multipart/form-data; boundary={boundary}",
                "params": [
                    {
                        "name": "file",
                        "value": "(binary)",
                        "fileName": file_name,
                        "contentType": "text/plain",
                    }
                ],
                "text": content,
            }
        )


def test_post_request_multipart_data_with_files(*, sync_formatter: SyncHARFormatter,
                                                respx_mock: RouterType,
                                                sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with sync_httpx_client() as client:
            data = {"id": "1", "name": "User"}
            file_name, file_content = "file.txt", b"file content"
            response = client.post("/", data=data, files={"file": (file_name, file_content)})

    with when:
        result = sync_formatter.format_request(response.request)

    with then:
        boundary, content = get_request_multipart(response.request, file_content)
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "355"},
                {"name": "content-type", "value": f"multipart/form-data; boundary={boundary}"},
            ],
            postData={
                "mimeType": f"multipart/form-data; boundary={boundary}",
                "text": content,
                "params": [
                    {"name": "id", "value": "1"},
                    {"name": "name", "value": "User"},
                    {
                        "name": "file",
                        "value": "(binary)",
                        "fileName": file_name,
                        "contentType": "text/plain",
                    }
                ]
            }
        )
