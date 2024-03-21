import httpx
from baby_steps import given, then, when

from vedro_httpx.har import HARFormatter

from ._utils import (
    HTTPClientType,
    RouterType,
    build_request,
    build_url,
    formatter,
    httpx_client,
    respx_mock,
)

__all__ = ("formatter", "respx_mock", "httpx_client",)  # fixtures


def test_get_request(*, formatter: HARFormatter, respx_mock: RouterType,
                     httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request()


def test_get_request_with_path(*, formatter: HARFormatter, respx_mock: RouterType,
                               httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/users").respond(200)
        with httpx_client() as client:
            response = client.get("/users")

    with when:
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request(url=build_url("/users"))


def test_get_request_with_params(*, formatter: HARFormatter, respx_mock: RouterType,
                                 httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with httpx_client() as client:
            params = httpx.QueryParams([("id", 1), ("id", 2)])
            response = client.get("/", params=params)

    with when:
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request(
            url=build_url("/", params=params),
            queryString=[
                {"name": "id", "value": "1"},
                {"name": "id", "value": "2"}
            ]
        )


def test_get_request_with_headers(*, formatter: HARFormatter, respx_mock: RouterType,
                                  httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with httpx_client() as client:
            headers = httpx.Headers([("x-header", "value1"), ("x-header", "value2")])
            response = client.get("/", headers=headers)

    with when:
        print(response.status_code)
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request(headers=[
            {"name": "x-header", "value": "value1"},
            {"name": "x-header", "value": "value2"}
        ])


def test_get_request_with_cookies(*, formatter: HARFormatter, respx_mock: RouterType,
                                  httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)

        cookies = httpx.Cookies({"cookie1": "value1", "cookie2": "value2"})
        with httpx_client(cookies=cookies) as client:
            # Setting per-request cookies=<...> is being deprecated,
            # because the expected behaviour on cookie persistence is ambiguous
            response = client.get("/")

    with when:
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request(
            cookies=[
                {"name": "cookie1", "value": "value1"},
                {"name": "cookie2", "value": "value2"}
            ],
            headers=[
                {"name": "cookie", "value": "cookie1=value1; cookie2=value2"}
            ])


def test_post_request_no_data(*, formatter: HARFormatter, respx_mock: RouterType,
                              httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with httpx_client() as client:
            response = client.post("/")

    with when:
        result = formatter.format_request(response.request)

    with then:
        expected_result = build_request(method="POST")
        expected_result["headers"].insert(1, {"name": "content-length", "value": "0"})

        assert result == expected_result


def test_post_request_json_data(*, formatter: HARFormatter, respx_mock: RouterType,
                                httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with httpx_client() as client:
            response = client.post("/", json={"id": 1, "name": "User"})

    with when:
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "25"},
                {"name": "content-type", "value": "application/json"},
            ],
            postData={
                "mimeType": "application/json",
                "text": '{"id": 1, "name": "User"}'
            }
        )


def test_post_request_binary_data(*, formatter: HARFormatter, respx_mock: RouterType,
                                  httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with httpx_client() as client:
            response = client.post("/", content=b"binary", headers={
                "content-type": "application/octet-stream"
            })

    with when:
        print(response.request.headers)
        result = formatter.format_request(response.request)

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


def test_post_request_form_data(*, formatter: HARFormatter, respx_mock: RouterType,
                                httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with httpx_client() as client:
            response = client.post("/", data={"id": "1", "name": "User"})

    with when:
        result = formatter.format_request(response.request)

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


def test_post_request_multipart_data(*, formatter: HARFormatter, respx_mock: RouterType,
                                     httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with httpx_client() as client:
            response = client.post("/", files={"id": "1", "name": "User"})

    with when:
        result = formatter.format_request(response.request)

    with then:
        boundary = response.request.headers["content-type"].split("boundary=")[1]
        content = response.request.content.decode()

        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "329"},
                {"name": "content-type", "value": f"multipart/form-data; boundary={boundary}"},
            ],
            postData={
                "mimeType": f"multipart/form-data; boundary={boundary}",
                "text": content,
                "params": [
                    {"name": "id", "value": "(binary)"},
                    {"name": "name", "value": "(binary)"}
                ]
            }
        )


def test_post_request_multipart_data_with_files(*, formatter: HARFormatter, respx_mock: RouterType,
                                                httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/").respond(200)
        with httpx_client() as client:
            response = client.post("/", files={"file": ("file.txt", b"file content")})

    with when:
        result = formatter.format_request(response.request)

    with then:
        boundary = response.request.headers["content-type"].split("boundary=")[1]
        content = response.request.content.decode()

        assert result == build_request(
            method="POST",
            headers=[
                {"name": "content-length", "value": "182"},
                {"name": "content-type", "value": f"multipart/form-data; boundary={boundary}"},
            ],
            postData={
                "mimeType": f"multipart/form-data; boundary={boundary}",
                "text": content,
                "params": [
                    {"name": "file", "value": "file content"},
                ]
            }
        )
