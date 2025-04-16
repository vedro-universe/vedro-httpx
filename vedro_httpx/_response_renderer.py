import json
import os
from typing import Any, List, Tuple, Union
from urllib.parse import parse_qsl, unquote

from httpx import Response
from httpx._models import Headers, Request
from pygments.lexer import Lexer
from pygments.lexers import (
    HttpLexer,
    JsonLexer,
    TextLexer,
    UrlEncodedLexer,
    get_lexer_for_mimetype,
)
from pygments.util import ClassNotFound
from rich.console import RenderResult
from rich.syntax import Syntax

__all__ = ("ResponseRenderer",)


class ResponseRenderer:
    def __init__(self, *,
                 include_request: bool = False,
                 include_request_body: bool = False,
                 ) -> None:
        self._include_request = include_request
        self._include_request_body = include_request_body
        self._binary_preview_size = 10
        self._syntax_theme = "ansi_dark"

    def render(self, response: Response, *, width: int) -> RenderResult:
        """
        Renders the HTTP response in a rich format.

        :param response: The HTTP response to render.
        :param width: The width for rendering.
        :return: Rendered response as a rich console output.
        """
        if self._include_request and response._request:
            # httpx does not provide the HTTP version of the request
            yield from self.render_request(response.request,
                                           width=width, http_version=response.http_version)
        yield from self.render_response(response, width=width)

    def render_response(self, response: Response, *, width: int = 80) -> RenderResult:
        """
        Yield formatted sections of an HTTP response for rendering in a rich console.

        This function creates visually appealing and structured representations of HTTP response
        headers and body using syntax highlighting. It automatically selects appropriate lexers for
        different content types and applies themes and formatting options.

        :param response: The HTTP response object from httpx to render.
        :param width: The maximum width for the code blocks. If not set, defaults to console width.
        :return: Yields formatted rich syntax objects for headers and body.
        """
        yield "← Response"
        headers, http_lexer = self.format_response_headers(response)
        yield self._create_syntax(headers, http_lexer, width)

        body, lexer = self.format_response_body(response)
        yield self._create_syntax(body, lexer, width, indent_guides=True)

    def format_response_headers(self, response: Response) -> Tuple[str, Lexer]:
        lines = [f"{response.http_version} {response.status_code} {response.reason_phrase}"]
        lines.extend(self._format_header_lines(response.headers))
        return os.linesep.join(lines), HttpLexer()

    def format_response_body(self, response: Response) -> Tuple[Any, Union[Lexer, str]]:
        content_type = response.headers.get("Content-Type", "")
        mime_type, encoding = self._extract_mime_type(content_type)

        try:
            lexer = get_lexer_for_mimetype(mime_type.strip())
        except ClassNotFound:
            preview = response.content[:self._binary_preview_size]
            return f"<binary preview={preview!r} len={len(response.content)}>", TextLexer()

        code = self._decode(response.content, encoding)
        if isinstance(lexer, JsonLexer):
            try:
                code = self._format_json(code)
            except:  # noqa: E722
                return code, TextLexer()
        return code, lexer

    def render_request(self, request: Request, *,
                       width: int = 80, http_version: str = "HTTP/1.1") -> RenderResult:
        yield "→ Request"
        headers, http_lexer = self._format_request_headers(request, http_version=http_version)
        yield self._create_syntax(headers, http_lexer, width)

        if self._include_request_body:
            if request.read():
                body, lexer = self._format_request_body(request)
                yield self._create_syntax(body, lexer, width, indent_guides=True)

    def _format_request_headers(self, request: Request, http_version: str) -> Tuple[str, Lexer]:
        url = str(request.url)
        lines = [f"{request.method} {url} {http_version}"]
        lines.extend(self._format_header_lines(request.headers))
        return os.linesep.join(lines), HttpLexer()

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
            try:
                return value.decode(encoding, errors="replace")
            except LookupError:
                return value.decode("utf-8", errors="replace")

    def _extract_mime_type(self, content_type: str, encoding: str = "utf-8") -> Tuple[str, str]:
        mime_type, *params = content_type.split(";")

        for param in params:
            param = param.strip()
            if param.lower().startswith("charset="):
                encoding = param.split("=")[1]
                break

        return mime_type.strip(), encoding

    def _format_json(self, content: str) -> str:
        return json.dumps(json.loads(content), indent=4, ensure_ascii=False, sort_keys=False)

    def _format_urlencoded(self, content: str) -> str:
        form_data = parse_qsl(content, keep_blank_values=True, errors="replace")
        formatted = []
        for key, value in form_data:
            formatted.append(f"{key}={unquote(value, errors='replace')}")
        return f"&{os.linesep}".join(formatted)

    def _format_request_body(self, request: Request) -> Tuple[Any, Union[Lexer, str]]:
        content_type = request.headers.get("Content-Type", "")
        mime_type, encoding = self._extract_mime_type(content_type)

        try:
            lexer = get_lexer_for_mimetype(mime_type.strip())
        except ClassNotFound:
            preview = request.content[:self._binary_preview_size]
            return f"<binary preview={preview!r} len={len(request.content)}>", TextLexer()

        code = self._decode(request.content, encoding)

        if isinstance(lexer, JsonLexer):
            try:
                code = self._format_json(code)
            except:  # noqa: E722
                return code, TextLexer()
        elif isinstance(lexer, UrlEncodedLexer):
            try:
                code = self._format_urlencoded(code)
            except:  # noqa: E722
                return code, TextLexer()

        return code, lexer

    def _format_header_lines(self, headers: Headers) -> List[str]:
        lines = []
        for header in headers:
            values = headers.get_list(header)
            for value in values:
                lines.append(f"{header}: {value}")
        return lines

    def _create_syntax(self, code: str, lexer: Union[Lexer, str], code_width: int,
                       **kwargs: Any) -> Syntax:
        return Syntax(code, lexer,
                      theme=self._syntax_theme, word_wrap=True, code_width=code_width, **kwargs)
