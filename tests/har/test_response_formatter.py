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
