from datetime import datetime
from typing import Any, Dict, Optional, Union, cast

import vedro
from httpx import URL
from httpx import AsyncClient as _AsyncClient
from httpx import Request
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault
from httpx._types import (
    AuthTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestFiles,
    TimeoutTypes,
)

from ._response import Response
from .recorder import RequestRecorder
from .recorder import request_recorder as default_request_recorder

__all__ = ("AsyncHTTPInterface", "AsyncClient",)


RequestData = Dict[Any, Any]


class AsyncClient(_AsyncClient):
    async def _send_single_request(self, request: Request) -> Response:
        request.extensions["vedro_httpx_started_at"] = datetime.now()

        response = await super()._send_single_request(request)

        return Response(
            status_code=response.status_code,
            headers=response.headers,
            stream=response.stream,
            request=response.request,
            extensions=response.extensions,
            default_encoding=response.default_encoding,
            history=response.history,
        )


class AsyncHTTPInterface(vedro.Interface):
    def __init__(self, base_url: Union[URL, str] = "", *,
                 request_recorder: RequestRecorder = default_request_recorder) -> None:
        super().__init__()
        self._base_url = base_url
        self._request_recorder = request_recorder

    # Docs https://www.python-httpx.org/api/#asyncclient
    def _client(self, **kwargs: Any) -> AsyncClient:
        base_url = kwargs.pop("base_url", self._base_url)
        client = AsyncClient(base_url=base_url, **kwargs)
        client.event_hooks["response"].append(self._request_recorder.async_record)
        return client

    # Arguments are duplicated to provide auto-completion
    async def _request(self,
                       method: str,
                       url: Union[URL, str],
                       *,
                       content: Optional[RequestContent] = None,
                       data: Optional[RequestData] = None,
                       files: Optional[RequestFiles] = None,
                       json: Optional[Any] = None,
                       params: Optional[QueryParamTypes] = None,
                       headers: Optional[HeaderTypes] = None,
                       auth: Union[AuthTypes, UseClientDefault, None] = USE_CLIENT_DEFAULT,
                       follow_redirects: Union[bool, UseClientDefault] = USE_CLIENT_DEFAULT,
                       timeout: Union[TimeoutTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
                       **kwargs: Any
                       ) -> Response:
        async with self._client() as client:
            return cast(Response, await client.request(
                method=method,
                url=url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                auth=auth,
                follow_redirects=follow_redirects,
                timeout=timeout,
                **kwargs
            ))
