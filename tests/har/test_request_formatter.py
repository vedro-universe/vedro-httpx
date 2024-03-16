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

        cookies = httpx.Cookies()
        with httpx_client(cookies=cookies) as client:
            # Setting per-request cookies=<...> is being deprecated,
            # because the expected behaviour on cookie persistence is ambiguous
            response = client.get("/")

    with when:
        result = formatter.format_request(response.request)

    with then:
        assert result == build_request(cookies=[])
