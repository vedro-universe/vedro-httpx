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
    """
    Provides utilities to render HTTPX Response and Request objects for rich console output.

    This class is responsible for transforming HTTP response and request data into visually
    formatted and syntax-highlighted blocks using the rich and pygments libraries. It supports
    optional rendering of the request and response bodies and headers.
    """

    def __init__(self, *,
                 include_request: bool = False,
                 include_request_body: bool = False,
                 include_response_body: bool = True,
                 body_binary_preview_size: int = 10,
                 body_json_indent: int = 4,
                 body_max_length: int = 4_096,
                 syntax_theme: str = "ansi_dark"
                 ) -> None:
        """
        Initialize the ResponseRenderer with configuration options.

        :param include_request: Whether to include request rendering.
        :param include_request_body: Whether to include the body of the request.
        :param include_response_body: Whether to include the body of the response.
        :param body_binary_preview_size: Maximum number of bytes to show for binary previews.
        :param body_json_indent: Number of spaces to use for JSON indentation.
        :param body_max_length: Maximum character length of body content to display.
        :param syntax_theme: Name of the syntax highlighting theme to use.
            Possible values can be found in the Rich documentation:
            https://rich.readthedocs.io/en/latest/syntax.html#theme
        """
        self._include_request = include_request
        self._include_request_body = include_request_body
        self._include_response_body = include_response_body
        self._body_binary_preview_size = body_binary_preview_size
        self._body_json_indent = body_json_indent
        self._body_max_length = body_max_length
        self._syntax_theme = syntax_theme

    def render(self, response: Response) -> RenderResult:
        """
        Render the HTTP response and optionally the request for rich console output.

        :param response: The HTTP response to render.
        :return: Rendered response as a generator of console segments.
        """
        if self._include_request and response._request:
            # httpx does not provide the HTTP version of the request
            yield from self.render_request(response.request, http_version=response.http_version)
        yield from self.render_response(response)

    def render_response(self, response: Response) -> RenderResult:
        """
        Render the HTTP response, including headers and optionally the body.

        :param response: The HTTP response to render.
        :return: Yields formatted response content for the rich console.
        """
        yield "← Response"
        headers, http_lexer = self.format_response_headers(response)
        yield self._create_syntax(headers, http_lexer)

        if self._include_response_body:
            body, lexer = self.format_response_body(response)
            yield self._create_syntax(body, lexer, indent_guides=True)

    def format_response_headers(self, response: Response) -> Tuple[str, Lexer]:
        """
        Format response headers for syntax highlighting.

        :param response: The HTTP response object.
        :return: Tuple containing a formatted string of headers and the appropriate lexer.
        """
        lines = [f"{response.http_version} {response.status_code} {response.reason_phrase}"]
        lines.extend(self._format_header_lines(response.headers))
        return os.linesep.join(lines), HttpLexer()

    def format_response_body(self, response: Response) -> Tuple[Any, Union[Lexer, str]]:
        """
        Format the response body based on its MIME type for console rendering.

        :param response: The HTTP response object.
        :return: Tuple of formatted response body and a lexer or fallback formatter.
        """
        content_type = response.headers.get("Content-Type", "")
        mime_type, encoding = self._extract_mime_type(content_type)

        try:
            lexer = get_lexer_for_mimetype(mime_type.strip())
        except ClassNotFound:
            preview = response.content[:self._body_binary_preview_size]
            return f"<binary preview={preview!r} len={len(response.content)}>", TextLexer()

        code = self._decode(response.content, encoding)
        if isinstance(lexer, JsonLexer):
            try:
                code = self._format_json(code)
            except:  # noqa: E722
                return self._maybe_truncate(code), TextLexer()
        return self._maybe_truncate(code), lexer

    def render_request(self, request: Request, *, http_version: str = "HTTP/1.1") -> RenderResult:
        """
        Render the HTTP request, including headers and optionally the body.

        :param request: The HTTP request to render.
        :param http_version: The HTTP version string to use in the request line.
        :return: Yields formatted request content for the rich console.
        """
        yield "→ Request"
        headers, http_lexer = self._format_request_headers(request, http_version=http_version)
        yield self._create_syntax(headers, http_lexer)

        if self._include_request_body:
            if request.read():
                body, lexer = self._format_request_body(request)
                yield self._create_syntax(body, lexer, indent_guides=True)

    def _format_request_headers(self, request: Request, http_version: str) -> Tuple[str, Lexer]:
        """
        Format request headers and start line for rendering.

        :param request: The HTTP request object.
        :param http_version: The HTTP version to include in the request line.
        :return: Tuple containing a formatted string and the appropriate lexer.
        """
        url = str(request.url)
        lines = [f"{request.method} {url} {http_version}"]
        lines.extend(self._format_header_lines(request.headers))
        return os.linesep.join(lines), HttpLexer()

    def _decode(self, value: bytes, encoding: str = "utf-8") -> str:
        """
        Decode byte content into a string using the provided encoding.

        :param value: Byte content to decode.
        :param encoding: Character encoding to use; defaults to UTF-8.
        :return: Decoded string content.
        :raises UnicodeDecodeError: If decoding fails without a fallback.
        :raises LookupError: If the specified encoding is not recognized.
        """
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            try:
                return value.decode(encoding, errors="replace")
            except LookupError:
                return value.decode("utf-8", errors="replace")

    def _extract_mime_type(self, content_type: str, encoding: str = "utf-8") -> Tuple[str, str]:
        """
        Extract the MIME type and encoding from a Content-Type header.

        :param content_type: The Content-Type header value.
        :param encoding: The default encoding to return if charset is not specified.
        :return: Tuple of MIME type and character encoding.
        """
        mime_type, *params = content_type.split(";")

        for param in params:
            param = param.strip()
            if param.lower().startswith("charset="):
                encoding = param.split("=")[1]
                break

        return mime_type.strip(), encoding

    def _format_json(self, content: str) -> str:
        """
        Format a JSON string with pretty printing and indentation.

        :param content: A string containing JSON data.
        :return: Formatted JSON string.
        :raises JSONDecodeError: If content is not valid JSON.
        """
        return json.dumps(json.loads(content), indent=self._body_json_indent, ensure_ascii=False)

    def _format_urlencoded(self, content: str) -> str:
        """
        Format URL-encoded form data into a readable string format.

        :param content: URL-encoded data string.
        :return: Readable string format of the form data.
        """
        form_data = parse_qsl(content, keep_blank_values=True, errors="replace")
        formatted = []
        for key, value in form_data:
            formatted.append(f"{key}={unquote(value, errors='replace')}")
        return f"&{os.linesep}".join(formatted)

    def _format_request_body(self, request: Request) -> Tuple[Any, Union[Lexer, str]]:
        """
        Format the body of the HTTP request for rendering.

        :param request: The HTTP request object.
        :return: Tuple of formatted body content and a lexer or fallback formatter.
        """
        content_type = request.headers.get("Content-Type", "")
        mime_type, encoding = self._extract_mime_type(content_type)

        try:
            lexer = get_lexer_for_mimetype(mime_type.strip())
        except ClassNotFound:
            preview = request.content[:self._body_binary_preview_size]
            return f"<binary preview={preview!r} len={len(request.content)}>", TextLexer()

        code = self._decode(request.content, encoding)

        if isinstance(lexer, JsonLexer):
            try:
                code = self._format_json(code)
            except:  # noqa: E722
                return self._maybe_truncate(code), TextLexer()
        elif isinstance(lexer, UrlEncodedLexer):
            try:
                code = self._format_urlencoded(code)
            except:  # noqa: E722
                return self._maybe_truncate(code), TextLexer()

        return self._maybe_truncate(code), lexer

    def _format_header_lines(self, headers: Headers) -> List[str]:
        """
        Format HTTP header lines into a list of strings.

        :param headers: HTTP headers object.
        :return: List of formatted header lines.
        """
        lines = []
        for header in headers:
            values = headers.get_list(header)
            for value in values:
                lines.append(f"{header}: {value}")
        return lines

    def _create_syntax(self, code: str, lexer: Union[Lexer, str], **kwargs: Any) -> Syntax:
        """
        Create a rich Syntax object for syntax-highlighted rendering.

        :param code: Code content to highlight.
        :param lexer: Lexer instance or name to use for syntax highlighting.
        :param kwargs: Additional keyword arguments for Syntax.
        :return: A rich Syntax object.
        """
        return Syntax(code, lexer, theme=self._syntax_theme, word_wrap=True, **kwargs)

    def _maybe_truncate(self, text: Union[str, bytes]) -> Union[str, bytes]:
        """
        Truncate text if it exceeds the configured body_max_length.

        :param text: The text or bytes object to potentially truncate.
        :return: Truncated text or original text if within limit.
        """
        if len(text) <= self._body_max_length:
            return text
        if isinstance(text, str):
            return text[:self._body_max_length] + f"… [truncated to {self._body_max_length} chars]"
        return text[:self._body_max_length]
