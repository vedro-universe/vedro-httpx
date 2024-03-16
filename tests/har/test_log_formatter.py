from baby_steps import given, then, when

from vedro_httpx import __version__ as version
from vedro_httpx.har import HARFormatter

from ._utils import (
    HTTPClientType,
    RouterType,
    build_request,
    build_response,
    formatter,
    httpx_client,
    respx_mock,
)

__all__ = ("formatter", "respx_mock", "httpx_client",)  # fixtures


def test_format_responses(*, formatter: HARFormatter, respx_mock: RouterType,
                          httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with httpx_client() as client:
            response = client.get("/")

    with when:
        result = formatter.format([response])

    with then:
        assert result == {
            "version": "1.2",
            "creator": {
                "name": "vedro-httpx",
                "version": version,
            },
            "entries": [
                {
                    "startedDateTime": "2021-01-01T00:00:00.000Z",
                    "time": 0,
                    "request": build_request(),
                    "response": build_response(),
                    "cache": {},
                    "timings": {
                        "send": 0,
                        "wait": 0,
                        "receive": 0,
                    }
                }
            ]
        }
