from datetime import datetime

import httpx
from baby_steps import given, then, when

from tests._utils import (
    AsyncHTTPClientType,
    HTTPClientType,
    RouterType,
    async_formatter,
    async_httpx_client,
    async_transport,
    build_request,
    build_response,
    build_url,
    builder,
    respx_mock,
    sync_formatter,
    sync_httpx_client,
    sync_transport,
)
from vedro_httpx import __version__ as version
from vedro_httpx.recorder import AsyncHARFormatter, SyncHARFormatter

__all__ = ("sync_formatter", "async_formatter", "sync_httpx_client", "async_httpx_client",
           "sync_transport", "async_transport", "builder", "respx_mock",)  # fixtures


def test_sync_format_responses(*, sync_formatter: SyncHARFormatter, respx_mock: RouterType,
                               sync_httpx_client: HTTPClientType):
    with given:
        respx_mock.post("/path").respond(200, json={"key": "value"})

        headers = {"x-header1": "value1", "x-header2": "value2"}
        params = {"param1": "value2", "param2": "value2"}
        payload = {"key1": "value1", "key2": "value2"}
        with sync_httpx_client() as client:
            response = client.post("/path", headers=headers, params=params, json=payload)

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
                    "request": build_request(
                        method="POST",
                        url=build_url("/path", httpx.QueryParams(params)),
                        queryString=[
                            {"name": "param1", "value": "value2"},
                            {"name": "param2", "value": "value2"},
                        ],
                        headers=[
                            {"name": "x-header1", "value": "value1"},
                            {"name": "x-header2", "value": "value2"},
                            {"name": "content-length", "value": "33"},
                            {"name": "content-type", "value": "application/json"},
                        ],
                        postData={
                            "mimeType": "application/json",
                            "text": '{"key1":"value1","key2":"value2"}',
                        }
                    ),
                    "response": build_response(
                        headers=[
                            {"name": "content-length", "value": "15"},
                            {"name": "content-type", "value": "application/json"},
                        ],
                        content={
                            "mimeType": "application/json",
                            "size": 15,
                            "text": '{"key":"value"}',
                        },
                    ),
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


async def test_async_format_responses(*, async_formatter: AsyncHARFormatter,
                                      respx_mock: RouterType,
                                      async_httpx_client: AsyncHTTPClientType):
    with given:
        respx_mock.post("/path").respond(200, json={"key": "value"})

        headers = {"x-header1": "value1", "x-header2": "value2"}
        params = {"param1": "value2", "param2": "value2"}
        payload = {"key1": "value1", "key2": "value2"}
        async with async_httpx_client() as client:
            response = await client.post("/path", headers=headers, params=params, json=payload)

        now = datetime.now()
        response.request.extensions["vedro_httpx_started_at"] = now

    with when:
        result = await async_formatter.format([response])

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
                    "request": build_request(
                        method="POST",
                        url=build_url("/path", httpx.QueryParams(params)),
                        queryString=[
                            {"name": "param1", "value": "value2"},
                            {"name": "param2", "value": "value2"},
                        ],
                        headers=[
                            {"name": "x-header1", "value": "value1"},
                            {"name": "x-header2", "value": "value2"},
                            {"name": "content-length", "value": "33"},
                            {"name": "content-type", "value": "application/json"},
                        ],
                        postData={
                            "mimeType": "application/json",
                            "text": '{"key1":"value1","key2":"value2"}',
                        }
                    ),
                    "response": build_response(
                        headers=[
                            {"name": "content-length", "value": "15"},
                            {"name": "content-type", "value": "application/json"},
                        ],
                        content={
                            "mimeType": "application/json",
                            "size": 15,
                            "text": '{"key":"value"}',
                        },
                    ),
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
