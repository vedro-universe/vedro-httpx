from typing import Any, Dict, Optional, Union, cast

import vedro
from httpx import URL
from httpx import Client as _SyncClient
from httpx import Request
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault
from httpx._types import (
    AuthTypes,
    CookieTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestFiles,
    TimeoutTypes,
)

from ._response import Response

__all__ = ("SyncHTTPInterface", "SyncClient",)

RequestData = Dict[Any, Any]


class SyncClient(_SyncClient):
    def _send_single_request(self, request: Request) -> Response:
        response = super()._send_single_request(request)
        return Response(
            status_code=response.status_code,
            headers=response.headers,
            stream=response.stream,
            request=response.request,
            extensions=response.extensions,
            default_encoding=response.default_encoding,
            history=response.history,
        )


class SyncHTTPInterface(vedro.Interface):
    def __init__(self, base_url: Union[URL, str] = "") -> None:
        super().__init__()
        self._base_url = base_url

    # Docs https://www.python-httpx.org/api/#client
    def _client(self, **kwargs: Any) -> SyncClient:
        return SyncClient(**kwargs)

    # Arguments are duplicated to provide auto-completion
    def _request(self,
                 method: str,
                 url: Union[URL, str],
                 *,
                 content: Optional[RequestContent] = None,
                 data: Optional[RequestData] = None,
                 files: Optional[RequestFiles] = None,
                 json: Optional[Any] = None,
                 params: Optional[QueryParamTypes] = None,
                 headers: Optional[HeaderTypes] = None,
                 cookies: Optional[CookieTypes] = None,
                 auth: Union[AuthTypes, UseClientDefault, None] = USE_CLIENT_DEFAULT,
                 follow_redirects: Union[bool, UseClientDefault] = USE_CLIENT_DEFAULT,
                 timeout: Union[TimeoutTypes, UseClientDefault] = USE_CLIENT_DEFAULT,
                 **kwargs: Any
                 ) -> Response:
        with self._client(base_url=self._base_url, trust_env=False) as client:
            return cast(Response, client.request(
                method=method,
                url=url,
                content=content,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                auth=auth,
                follow_redirects=follow_redirects,
                timeout=timeout,
                **kwargs
            ))
