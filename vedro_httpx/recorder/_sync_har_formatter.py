from typing import List

import httpx

import vedro_httpx.recorder.har as har

from ._base_har_formatter import BaseHARFormatter

__all__ = ("SyncHARFormatter",)


class SyncHARFormatter(BaseHARFormatter):
    def format(self, responses: List[httpx.Response]) -> har.Log:
        entries = []
        for response in responses:
            entry = self.format_entry(response, response.request)
            entries.append(entry)

        return self._builder.build_log(entries)

    def format_entry(self, response: httpx.Response, request: httpx.Request) -> har.Entry:
        formatted_response = self.format_response(response)
        # httpx does not provide the HTTP version of the request
        formatted_request = self.format_request(request, http_version=response.http_version)

        started_at = self._format_request_started_at(request)
        time = self._format_elapsed(response)
        server_ip_address = self._get_server_ip_address(response)
        return self._builder.build_entry(formatted_request, formatted_response, started_at, time,
                                         server_ip_address)

    def format_request(self, request: httpx.Request, *,
                       http_version: str = "HTTP/1.1") -> har.Request:
        if content := request.read():
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

    def format_response(self, response: httpx.Response) -> har.Response:
        return self._builder.build_response(
            status=response.status_code,
            status_text=response.reason_phrase,
            http_version=response.http_version,
            cookies=self._format_cookies(self._get_response_cookies(response.headers)),
            headers=self._format_headers(response.headers),
            content=self.format_response_content(response),
            redirect_url=self._get_location_header(response.headers),
        )

    def format_response_content(self, response: httpx.Response) -> har.Content:
        content_type = self._get_content_type(response.headers)
        try:
            content = response.read()
        except httpx.StreamConsumed:
            return self._builder.build_response_content(content_type, size=0, text="(stream)",
                                                        comment="Stream consumed")
        return self._format_response_content(content, content_type)
