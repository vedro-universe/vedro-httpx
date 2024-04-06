from datetime import datetime

from baby_steps import given, then, when

from vedro_httpx import __version__ as version
from vedro_httpx.har import SyncHARFormatter

from ._utils import (
    HTTPClientType,
    RouterType,
    build_request,
    build_response,
    builder,
    respx_mock,
    sync_formatter,
    sync_httpx_client,
)

__all__ = ("sync_formatter", "builder", "respx_mock", "sync_httpx_client",)  # fixtures


def test_format_responses(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                          sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.get("/").respond(200)
        with sync_httpx_client() as client:
            response = client.get("/")

        now = datetime.now()
        response.request.extensions["vedro_httpx_started_at"] = now

    with when:
        result = sync_formatter.format([response])

    with then:
        assert result == {
            "version": "1.2",
            "creator": {
                "name": "vedro-httpx",
                "version": version,
            },
            "entries": [
                {
                    "startedDateTime": now.isoformat(),
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
            ],
            "pages": [],
        }
