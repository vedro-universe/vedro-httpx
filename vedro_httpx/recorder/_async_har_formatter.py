from typing import List

import httpx

import vedro_httpx.recorder.har as har

from ._base_har_formatter import BaseHARFormatter

__all__ = ("AsyncHARFormatter",)


class AsyncHARFormatter(BaseHARFormatter):
    """
    Formatter for creating HAR (HTTP Archive) entries and logs from HTTP responses obtained
    through asynchronous requests using httpx.AsyncClient. This class utilizes the common
    formatting functionalities provided by BaseHARFormatter to process and transform HTTP request
    and response data into the standardized HAR format.
    """

    async def format(self, responses: List[httpx.Response]) -> har.Log:
        """
        Create a HAR log from a list of HTTP responses.

        Iterates over each response, formats it along with its corresponding request into a HAR
        entry, and then compiles these entries into a HAR log.

        :param responses: A list of httpx.Response objects to be formatted.
        :return: A HAR log dictionary that encapsulates all the formatted entries.
        """
        entries = []
        for response in responses:
            entry = await self.format_entry(response, response.request)
            entries.append(entry)

        return self._builder.build_log(entries)

    async def format_entry(self, response: httpx.Response, request: httpx.Request) -> har.Entry:
        """
        Format a single HTTP response and its associated request into a HAR entry.

        :param response: The httpx.Response object to format.
        :param request: The httpx.Request object associated with the response to format.
        :return: A HAR entry dictionary encapsulating the formatted request and response.
        """
        formatted_response = await self.format_response(response)
        # httpx does not provide the HTTP version of the request
        formatted_request = await self.format_request(request, http_version=response.http_version)

        started_at = self._format_request_started_at(request)
        time = self._format_elapsed(response)
        server_ip_address = self._get_server_ip_address(response)
        return self._builder.build_entry(formatted_request, formatted_response, started_at, time,
                                         server_ip_address)

    async def format_request(self, request: httpx.Request, *,
                             http_version: str = "HTTP/1.1") -> har.Request:
        """
        Format an HTTP request into a HAR request object.

        :param request: The httpx.Request object to format.
        :param http_version: The HTTP version to use in the formatting (default "HTTP/1.1").
        :return: A HAR request dictionary.
        """
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
        """
        Format an HTTP response into a HAR response object.

        :param response: The httpx.Response object to format.
        :return: A HAR response dictionary encapsulating the formatted response details.
        """
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
        """
        Format the content of an HTTP response into a HAR content object.

        :param response: The httpx.Response object whose content is to be formatted.
        :return: A HAR content dictionary.
        """
        content_type = self._get_content_type(response.headers)
        try:
            content = await response.aread()
        except httpx.StreamConsumed:
            return self._builder.build_response_content(content_type, size=0, text="(stream)",
                                                        comment="Stream consumed")
        return self._format_response_content(content, content_type)
