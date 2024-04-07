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
    def __init__(self, har_builder: HARBuilder) -> None:
        self._builder = har_builder

    def _format_cookies(self, headers: List[str]) -> List[har.Cookie]:
        cookies = []
        for header in headers:
            cookie = SimpleCookie()
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
            except Exception:
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
            text = self._decode(content)
            return self._builder.build_post_data(content_type, text)

        return self._builder.build_post_data(content_type, "binary")

    def _format_url_encoded(self, content: bytes) -> Tuple[str, List[har.PostParam]]:
        payload = self._decode(content)
        try:
            parsed = parse_qsl(payload)
        except Exception:
            return payload, []
        post_params = [self._builder.build_post_param(name, value) for name, value in parsed]
        return payload, post_params

    def _format_multipart(self, content: bytes,
                          content_type: str) -> Tuple[str, List[har.PostParam]]:
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
        message: Message = Parser(policy=HTTPPolicy).parsestr(multipart)
        for part in message.get_payload():
            assert isinstance(part, EmailMessage)
            if part.get_param("filename", header="Content-Disposition"):
                part.set_payload("(binary)")
        return message

    def _format_elapsed(self, response: httpx.Response) -> int:
        try:
            elapsed = response.elapsed
        except RuntimeError:
            elapsed = datetime.now() - self._get_request_started_at(response.request)
        return int(elapsed.total_seconds() * 1000)

    def _format_response_content(self, content: bytes, content_type: str) -> har.Content:
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
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            return value.decode(encoding, errors="surrogateescape")

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

    def _get_server_ip_address(self, response: httpx.Response) -> Union[str, None]:
        network_stream = response.extensions.get("network_stream")
        if network_stream is None:
            return None
        server_addr = network_stream.get_extra_info("server_addr")
        if server_addr is None:
            return None
        return str(server_addr[0])

    def _get_request_started_at(self, request: httpx.Request) -> datetime:
        started_at = request.extensions.get("vedro_httpx_started_at", datetime.now())
        return cast(datetime, started_at)

    def _format_request_started_at(self, request: httpx.Request) -> str:
        return self._get_request_started_at(request).isoformat()
