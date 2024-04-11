from datetime import datetime
from typing import Any, Optional, Union, cast

import vedro
from httpx import AsyncClient as _AsyncClient
from httpx import Request
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault
from httpx._types import (
    AuthTypes,
    HeaderTypes,
    QueryParamTypes,
    RequestContent,
    RequestData,
    RequestExtensions,
    RequestFiles,
    TimeoutTypes,
    URLTypes,
)

from ._response import Response
from .recorder import RequestRecorder
from .recorder import request_recorder as default_request_recorder

__all__ = ("AsyncHTTPInterface", "AsyncClient",)


class AsyncClient(_AsyncClient):
    """
    Extends the httpx.AsyncClient to include custom response handling.

    This subclass customizes the response object to use the enhanced Response class
    which supports rendering in rich console environments.
    """

    async def _send_single_request(self, request: Request) -> Response:
        """
        Send an HTTP request asynchronously and return an enhanced response object.

        :param request: The HTTP request object to be sent.
        :return: An enhanced Response object containing the HTTP response data.
        """
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
    """
    Provides an asynchronous HTTP interface for making requests using a base URL.

    This interface is designed to wrap HTTP operations with additional functionalities such as
    request recording.
    """

    def __init__(self, base_url: URLTypes = "", *,
                 request_recorder: RequestRecorder = default_request_recorder) -> None:
        """
       Initialize the AsyncHTTPInterface with a base URL and a request recorder.

       :param base_url: The base URL to be prefixed to all requests. Defaults to an empty string.
       :param request_recorder: The recorder instance used for tracking requests.
       """
        super().__init__()
        self._base_url = base_url
        self._request_recorder = request_recorder

    def _client(self, **kwargs: Any) -> AsyncClient:
        """
        Constructs an AsyncClient configured with a base URL and event hooks for
        response recording.

        :param kwargs: Keyword arguments to override default client configurations.
        :return: An instance of `SyncClient` configured with a base URL and response hooks.
        """
        base_url = kwargs.pop("base_url", self._base_url)
        client = AsyncClient(base_url=base_url, **kwargs)
        client.event_hooks["response"].append(self._request_recorder.async_record)
        return client

    async def _request(self,
                       method: str,
                       url: URLTypes,
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
                       extensions: Optional[RequestExtensions] = None,
                       **kwargs: Any
                       ) -> Response:
        """
        Send an HTTP request and return a Response object.

        Parameters are intentionally duplicated in the method signature and the docstring
        to enhance autocomplete functionality in various IDEs, which helps in providing
        quick access to expected parameters and their types during method usage.

        :param method: HTTP method to use for the request (e.g., 'GET', 'POST').
        :param url: The URL to send the request to. Can be absolute or relative to the base URL.
        :param content: Binary content to include in the body of the request.
        :param data: Form data to include in the body of the request, as a dictionary or sequence
                     of two-tuples.
        :param files: Files to upload.
        :param json: JSON data to include in the body of the request.
        :param params: Query parameters for the URL.
        :param headers: HTTP headers to include in the request.
        :param auth: Authentication mechanism to use.
        :param follow_redirects: Whether to follow server redirects.
        :param timeout: Timeout configuration for the request.
        :param extensions: Additional extensions to pass to the request.
        :param kwargs: Additional keyword arguments to pass to the request method.
        :return: A `Response` object containing the server's response to the HTTP request.
        """
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
                extensions=extensions,
                **kwargs
            ))
