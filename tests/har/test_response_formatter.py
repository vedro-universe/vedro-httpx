from baby_steps import given, then, when

from vedro_httpx.har import HARFormatter

from ._utils import HTTPClientType, RouterType, build_response, formatter, httpx_client, respx_mock

__all__ = ("formatter", "respx_mock", "httpx_client",)  # fixtures


def test_response(*, formatter: HARFormatter, respx_mock: RouterType,
                  httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format_response(response)

    with then:
        assert result == build_response()


def test_response_with_status(*, formatter: HARFormatter, respx_mock: RouterType,
                              httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(404)
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format_response(response)

    with then:
        assert result == build_response(status=404, statusText="Not Found")


def test_response_with_headers(*, formatter: HARFormatter, respx_mock: RouterType,
                               httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200, headers=[
            ("x-header", "value1"),
            ("x-header", "value2")
        ])
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format_response(response)

    with then:
        assert result == build_response(headers=[
            {"name": "x-header", "value": "value1"},
            {"name": "x-header", "value": "value2"}
        ])


def test_response_with_redirect(*, formatter: HARFormatter, respx_mock: RouterType,
                                httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(301, headers=[
            ("location", "/redirected")
        ])
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format_response(response)

    with then:
        assert result == build_response(
            status=301,
            statusText="Moved Permanently",
            headers=[
                {"name": "location", "value": "/redirected"}
            ],
            redirectURL="/redirected"
        )


def test_response_with_cookies(*, formatter: HARFormatter, respx_mock: RouterType,
                               httpx_client: HTTPClientType):
    with given:
        cookie_attrs = ("Domain=localhost; expires=Sat, 01-Jan-2024 00:00:00 GMT; HttpOnly; "
                        "Max-Age=3600; Path=/; SameSite=Strict; Secure; Version=1")

        respx_mock.get("/").respond(200, headers=[
            ("set-cookie", "name1=value1"),
            ("set-cookie", f"name2=value2; {cookie_attrs}"),
        ])
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format_response(response)

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
