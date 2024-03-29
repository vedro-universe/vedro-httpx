from base64 import b64encode
from email.message import Message
from email.parser import Parser
from email.policy import HTTP as HTTPPolicy
from email.utils import parsedate_to_datetime
from http.cookies import Morsel, SimpleCookie
from typing import Any, List, Tuple, cast
from urllib.parse import parse_qsl

import httpx

import vedro_httpx
import vedro_httpx.har._types as har

from ._har_builder import HARBuilder

__all__ = ("HARFormatter",)


class BaseHARFormatter:
    def __init__(self, creator_name: str = "vedro-httpx",
                 creator_version: str = vedro_httpx.__version__) -> None:
        self._builder = HARBuilder()
        self._creator_name = creator_name
        self._creator_version = creator_version

    def _format_cookies(self, headers: List[str]) -> List[har.Cookie]:
        cookies = []
        for header in headers:
            cookie: SimpleCookie[Any] = SimpleCookie()
            cookie.load(header)
            for name, morsel in cookie.items():
                cookies.append(self._format_cookie(name, morsel))
        return cookies

    def _format_headers(self, headers: httpx.Headers) -> List[har.Header]:
        return [self._builder.build_header(name, val) for name, val in headers.multi_items()]

    def _format_query_params(self, params: httpx.QueryParams) -> List[har.QueryParam]:
        return [self._builder.build_query_param(name, val) for name, val in params.multi_items()]

    def _format_cookie(self, name: str, morsel: "Morsel[Any]") -> har.Cookie:
        path = morsel["path"] if morsel["path"] else None
        domain = morsel["domain"] if morsel["domain"] else None
        http_only = morsel["httponly"] if morsel["httponly"] else None
        secure = morsel["secure"] if morsel["secure"] else None
        expires = morsel["expires"] if morsel["expires"] else None
        comment = None

        if expires:
            try:
                expires = parsedate_to_datetime(expires).isoformat()
            except BaseException:
                expires = None
                comment = f"Invalid date format: {morsel['expires']}"

        return self._builder.build_cookie(name, morsel.value, path, domain, expires,
                                          http_only, secure, comment=comment)

    def _format_request_post_data(self, content: bytes, content_type: str) -> har.PostData:
        if content_type.startswith("application/x-www-form-urlencoded"):
            text, params = self._format_url_encoded(content)
            return self._builder.build_post_data(content_type, text, params)

        if content_type.startswith("multipart/form-data"):
            text, params = self._format_multipart(content, content_type)
            return self._builder.build_post_data(content_type, text, params)

        if self._is_text_content(content_type):
            text = content.decode()
            return self._builder.build_post_data(content_type, text)

        return self._builder.build_post_data(content_type, "binary")

    def _format_url_encoded(self, content: bytes) -> Tuple[str, List[har.PostParam]]:
        payload = content.decode()
        try:
            parsed = parse_qsl(payload)
        except BaseException:
            return payload, []
        post_params = [self._builder.build_post_param(name, value) for name, value in parsed]
        return payload, post_params

    def _format_multipart(self, content: bytes,
                          content_type: str) -> Tuple[str, List[har.PostParam]]:
        header = f"Content-Type: {content_type}\r\n\r\n"
        payload = content.decode("ASCII", errors="surrogateescape")

        post_params = []
        multipart = self._parse_multipart(f"{header}{payload}")
        for part in multipart.get_payload():
            name = part.get_param("name", header="Content-Disposition")
            value = part.get_payload(decode=True).decode()
            filename = part.get_param("filename", header="Content-Disposition")

            if filename:
                part_type = part.get_content_type()
                post_param = self._builder.build_post_param(name, value, filename, part_type)
            else:
                post_param = self._builder.build_post_param(name, value)
            post_params.append(post_param)

        content_str = multipart.as_string()
        return content_str.replace(header, "", 1), post_params

    def _parse_multipart(self, multipart: str) -> Message:
        message: Message = Parser(policy=HTTPPolicy).parsestr(multipart)
        for part in message.get_payload():
            if part.get_param("filename", header="Content-Disposition"):
                part.set_payload("(binary)")
        return message

    def _format_elapsed(self, response: httpx.Response) -> int:
        try:
            elapsed = response.elapsed
        except RuntimeError:
            return 0
        return int(elapsed.total_seconds() * 1000)

    def _format_response_content(self, content: bytes, content_type: str) -> har.Content:
        size = len(content)
        if size == 0:
            return self._builder.build_response_content(content_type, size)

        if self._is_text_content(content_type):
            text = content.decode()
            return self._builder.build_response_content(content_type, size, text)
        else:
            text = b64encode(content).decode()
            return self._builder.build_response_content(content_type, size, text,
                                                        encoding="base64")

    def _is_text_content(self, content_type: str) -> bool:
        return (
            content_type.startswith("text/") or
            content_type.startswith("application/json") or
            content_type.startswith("application/xml")
        )

    def _get_request_cookies(self, headers: httpx.Headers) -> List[str]:
        return headers.get_list("Cookie")

    def _get_response_cookies(self, headers: httpx.Headers) -> List[str]:
        return headers.get_list("Set-Cookie")

    def _get_location_header(self, headers: httpx.Headers) -> str:
        return cast(str, headers.get("Location", ""))

    def _get_content_type(self, headers: httpx.Headers) -> str:
        return cast(str, headers.get("Content-Type", "x-unknown"))


class HARFormatter(BaseHARFormatter):
    def format(self, responses: List[httpx.Response]) -> har.Log:
        creator = self._builder.build_creator(self._creator_name, self._creator_version)

        entries = []
        for response in responses:
            entry = self.format_entry(response, response.request)
            entries.append(entry)

        return self._builder.build_log(creator, entries)

    def format_entry(self, response: httpx.Response, request: httpx.Request) -> har.Entry:
        formatted_response = self.format_response(response)
        # httpx does not provide the HTTP version of the request
        formatted_request = self.format_request(request, http_version=response.http_version)

        started_at = "2021-01-01T00:00:00.000Z"
        time = self._format_elapsed(response)
        return self._builder.build_entry(formatted_request, formatted_response, started_at, time)

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
