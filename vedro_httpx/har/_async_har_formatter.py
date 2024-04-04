from typing import List

import httpx

import vedro_httpx.har._types as har

from ._base_har_formatter import BaseHARFormatter

__all__ = ("AsyncHARFormatter",)


class AsyncHARFormatter(BaseHARFormatter):
    async def format(self, responses: List[httpx.Response]) -> har.Log:
        creator = self._builder.build_creator(self._creator_name, self._creator_version)

        entries = []
        for response in responses:
            entry = await self.format_entry(response, response.request)
            entries.append(entry)

        return self._builder.build_log(creator, entries)

    async def format_entry(self, response: httpx.Response, request: httpx.Request) -> har.Entry:
        formatted_response = await self.format_response(response)
        # httpx does not provide the HTTP version of the request
        formatted_request = await self.format_request(request, http_version=response.http_version)

        started_at = "2021-01-01T00:00:00.000Z"
        time = self._format_elapsed(response)
        return self._builder.build_entry(formatted_request, formatted_response, started_at, time)

    async def format_request(self, request: httpx.Request, *,
                             http_version: str = "HTTP/1.1") -> har.Request:
        if content := await request.aread():
            content_type = self._get_content_type(request.headers)
            post_data = self._format_request_post_data(content, content_type)
        else:
            post_data = None

        return self._builder.build_request(
            method=request.method,
            url=str(request.url),
            http_version=http_version,
            query_string=self._format_query_params(request.url.params),
            headers=self._format_headers(request.headers),
            cookies=self._format_cookies(self._get_request_cookies(request.headers)),
            post_data=post_data,
        )

    async def format_response(self, response: httpx.Response) -> har.Response:
        return self._builder.build_response(
            status=response.status_code,
            status_text=response.reason_phrase,
            http_version=response.http_version,
            cookies=self._format_cookies(self._get_response_cookies(response.headers)),
            headers=self._format_headers(response.headers),
            content=await self.format_response_content(response),
            redirect_url=self._get_location_header(response.headers),
        )

    async def format_response_content(self, response: httpx.Response) -> har.Content:
        content_type = self._get_content_type(response.headers)
        try:
            content = await response.aread()
        except httpx.StreamConsumed:
            return self._builder.build_response_content(content_type, size=0, text="(stream)",
                                                        comment="Stream consumed")
        return self._format_response_content(content, content_type)
