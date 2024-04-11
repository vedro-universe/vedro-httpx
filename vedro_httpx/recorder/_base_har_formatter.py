from base64 import b64encode
from datetime import datetime
from email.message import EmailMessage, Message
from email.parser import Parser
from email.policy import HTTP as HTTPPolicy
from email.utils import parsedate_to_datetime
from http.cookies import Morsel, SimpleCookie
from typing import Any, List, Tuple, Union, cast
from urllib.parse import parse_qsl

import httpx

import vedro_httpx.recorder.har as har

from ._har_builder import HARBuilder

__all__ = ("BaseHARFormatter",)


class BaseHARFormatter:
    """
    Base formatter class for creating HTTP Archive (HAR) format elements from HTTP transactions.
    This class provides common functionalities to extract and transform HTTP request and response
    data into the standardized HAR format. It uses a HARBuilder to construct the individual
    components of the HAR file, such as requests, responses, cookies, and headers.
    """

    def __init__(self, har_builder: HARBuilder) -> None:
        """
        Initialize the formatter with a HARBuilder instance.

        :param har_builder: The HARBuilder instance to use for creating HAR elements.
        """
        self._builder = har_builder

    def _format_cookies(self, headers: List[str]) -> List[har.Cookie]:
        """
        Extract and format cookies from HTTP headers into HAR cookies.

        :param headers: A list of cookie headers.
        :return: A list of HAR cookies.
        """
        cookies = []
        for header in headers:
            cookie = SimpleCookie()
            cookie.load(header)
            for name, morsel in cookie.items():
                cookies.append(self._format_cookie(name, morsel))
        return cookies

    def _format_headers(self, headers: httpx.Headers) -> List[har.Header]:
        """
        Convert HTTP headers into HAR headers.

        :param headers: The HTTP headers to format.
        :return: A list of HAR headers.
        """
        return [self._builder.build_header(name, val) for name, val in headers.multi_items()]

    def _format_query_params(self, params: httpx.QueryParams) -> List[har.QueryParam]:
        """
        Convert URL query parameters into HAR query parameters.

        :param params: The query parameters to format.
        :return: A list of HAR query parameters.
        """
        return [self._builder.build_query_param(name, val) for name, val in params.multi_items()]

    def _format_cookie(self, name: str, morsel: "Morsel[Any]") -> har.Cookie:
        """
        Create a HAR cookie from a cookie Morsel object.

        :param name: The name of the cookie.
        :param morsel: The Morsel object containing cookie details.
        :return: A formatted HAR cookie.
        """
        path = morsel["path"] if morsel["path"] else None
        domain = morsel["domain"] if morsel["domain"] else None
        http_only = morsel["httponly"] if morsel["httponly"] else None
        secure = morsel["secure"] if morsel["secure"] else None
        expires = morsel["expires"] if morsel["expires"] else None
        comment = None

        if expires:
            try:
                expires = parsedate_to_datetime(expires).isoformat()
            except Exception:
                expires = None
                comment = f"Invalid date format: {morsel['expires']}"

        return self._builder.build_cookie(name, morsel.value, path, domain, expires,
                                          http_only, secure, comment=comment)

    def _format_request_post_data(self, content: bytes, content_type: str) -> har.PostData:
        """
        Format the content of a HTTP request body into HAR post data.

        :param content: The byte content of the request body.
        :param content_type: The content type of the request body.
        :return: A HAR PostData object.
        """
        if content_type.startswith("application/x-www-form-urlencoded"):
            text, params = self._format_url_encoded(content)
            return self._builder.build_post_data(content_type, text, params)

        if content_type.startswith("multipart/form-data"):
            text, params = self._format_multipart(content, content_type)
            return self._builder.build_post_data(content_type, text, params)

        if self._is_text_content(content_type):
            text = self._decode(content)
            return self._builder.build_post_data(content_type, text)

        return self._builder.build_post_data(content_type, "binary")

    def _format_url_encoded(self, content: bytes) -> Tuple[str, List[har.PostParam]]:
        """
        Parse URL-encoded request data into HAR post parameters.

        :param content: The byte content of the URL-encoded data.
        :return: A tuple containing the URL-decoded string and a list of HAR post parameters.
        """
        payload = self._decode(content)
        try:
            parsed = parse_qsl(payload)
        except Exception:
            return payload, []
        post_params = [self._builder.build_post_param(name, value) for name, value in parsed]
        return payload, post_params

    def _format_multipart(self, content: bytes,
                          content_type: str) -> Tuple[str, List[har.PostParam]]:
        """
        Parse multipart/form-data request body into HAR post parameters.

        :param content: The byte content of the multipart data.
        :param content_type: The content type header of the multipart data.
        :return: A tuple containing the multipart string and a list of HAR post parameters.
        """
        header = f"Content-Type: {content_type}\r\n\r\n"
        payload = self._decode(content)

        post_params = []
        multipart = self._parse_multipart(f"{header}{payload}")
        for part in multipart.get_payload():
            assert isinstance(part, EmailMessage)
            name = part.get_param("name", header="Content-Disposition")
            value = self._decode(part.get_payload(decode=True))  # type: ignore
            filename = part.get_param("filename", header="Content-Disposition")

            if filename:
                part_type = part.get_content_type()
                post_param = self._builder.build_post_param(name, value,  # type: ignore
                                                            filename, part_type)  # type: ignore
            else:
                post_param = self._builder.build_post_param(name, value)  # type: ignore
            post_params.append(post_param)

        content_str = multipart.as_string()
        return content_str.replace(header, "", 1), post_params

    def _parse_multipart(self, multipart: str) -> Message:
        """
        Convert a string containing a multipart HTTP request body into an email message object.

        :param multipart: The multipart content as a string.
        :return: An email message object representing the multipart content.
        """
        message: Message = Parser(policy=HTTPPolicy).parsestr(multipart)
        for part in message.get_payload():
            assert isinstance(part, EmailMessage)
            if part.get_param("filename", header="Content-Disposition"):
                part.set_payload("(binary)")
        return message

    def _format_elapsed(self, response: httpx.Response) -> int:
        """
        Calculate the elapsed time of an HTTP response in milliseconds.

        :param response: The response object.
        :return: The elapsed time in milliseconds.
        """
        try:
            elapsed = response.elapsed
        except RuntimeError:
            elapsed = datetime.now() - self._get_request_started_at(response.request)
        return int(elapsed.total_seconds() * 1000)

    def _format_response_content(self, content: bytes, content_type: str) -> har.Content:
        """
        Format the response content into a HAR content object.

        :param content: The byte content of the response.
        :param content_type: The content type of the response.
        :return: A HAR content object representing the response body.
        """
        size = len(content)
        if size == 0:
            return self._builder.build_response_content(content_type, size)

        if self._is_text_content(content_type):
            text = self._decode(content)
            return self._builder.build_response_content(content_type, size, text)
        else:
            text = b64encode(content).decode()
            return self._builder.build_response_content(content_type, size, text,
                                                        encoding="base64")

    def _decode(self, value: bytes, encoding: str = "utf-8") -> str:
        """
        Decode byte content using a specified encoding.

        :param value: The byte content to decode.
        :param encoding: The encoding to use for decoding.
        :return: The decoded string.
        """
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            return value.decode(encoding, errors="surrogateescape")

    def _is_text_content(self, content_type: str) -> bool:
        """
        Determine if the given content type is text-based.

        :param content_type: The content type to evaluate.
        :return: True if the content type is text-based, otherwise False.
        """
        return (
            content_type.startswith("text/") or
            content_type.startswith("application/json") or
            content_type.startswith("application/xml")
        )

    def _get_request_cookies(self, headers: httpx.Headers) -> List[str]:
        """
        Retrieve the cookie headers from a request.

        :param headers: The HTTP headers from which to extract cookie data.
        :return: A list of cookie header strings.
        """
        return headers.get_list("Cookie")

    def _get_response_cookies(self, headers: httpx.Headers) -> List[str]:
        """
        Retrieve the Set-Cookie headers from a response.

        :param headers: The HTTP headers from which to extract Set-Cookie data.
        :return: A list of Set-Cookie header strings.
        """
        return headers.get_list("Set-Cookie")

    def _get_location_header(self, headers: httpx.Headers) -> str:
        """
        Extract the Location header from HTTP headers.

        :param headers: The HTTP headers from which to retrieve the Location header.
        :return: The value of the Location header, or an empty string if not present.
        """
        return cast(str, headers.get("Location", ""))

    def _get_content_type(self, headers: httpx.Headers) -> str:
        """
        Determine the content type specified in the HTTP headers.

        :param headers: The HTTP headers from which to retrieve the content type.
        :return: The content type as a string, or 'x-unknown' if not specified.
        """
        return cast(str, headers.get("Content-Type", "x-unknown"))

    def _get_server_ip_address(self, response: httpx.Response) -> Union[str, None]:
        """
        Retrieve the server IP address from a response.

        :param response: The response object from which to extract the server IP address.
        :return: The server IP address as a string, or None if not available.
        """
        network_stream = response.extensions.get("network_stream")
        if network_stream is None:
            return None
        server_addr = network_stream.get_extra_info("server_addr")
        if server_addr is None:
            return None
        return str(server_addr[0])

    def _get_request_started_at(self, request: httpx.Request) -> datetime:
        """
        Retrieve the timestamp when the request was initiated.

        :param request: The request object from which to extract the start time.
        :return: The datetime object representing when the request was started.
        """
        started_at = request.extensions.get("vedro_httpx_started_at", datetime.now())
        return cast(datetime, started_at)

    def _format_request_started_at(self, request: httpx.Request) -> str:
        """
        Format the request start time as an ISO 8601 string.

        :param request: The request object from which to extract and format the start time.
        :return: The formatted start time in ISO 8601 string format.
        """
        return self._get_request_started_at(request).isoformat()
