from typing import Any, Optional, Tuple, Union
from urllib.parse import parse_qs

from httpx._models import Request
from pygments.lexer import Lexer
from pygments.lexers import JsonLexer, TextLexer, UrlEncodedLexer, get_lexer_for_mimetype
from pygments.util import ClassNotFound
from rich.console import RenderResult
from rich.syntax import Syntax

__all__ = ("render_request")

from vedro_httpx._render_headers import format_request_headers
from vedro_httpx._render_json import get_pretty_json


def render_request(request: Request, *,
                   theme: str = "ansi_dark", width: Optional[int] = None) -> RenderResult:
    yield f"→ Request {request.method} {request.url}"
    headers, http_lexer = format_request_headers(request)
    yield Syntax(headers, http_lexer, theme=theme, word_wrap=True, code_width=width)

    body, lexer = format_request_body(request)
    if body is not None:
        yield Syntax(body, lexer, theme=theme, word_wrap=True, code_width=width)


def format_request_body(request: Request) -> Tuple[Any, Union[Lexer, str]]:
    content_type = request.headers.get("Content-Type", "")
    mime_type, *_ = content_type.split(";")

    try:
        lexer = get_lexer_for_mimetype(mime_type.strip())
    except ClassNotFound:
        content = request.read() if mime_type == 'multipart/form-data' else request.content
        if len(content) == 0:
            return None, ""
        return f"<binary preview={content[:10]!r} len={len(content)}>", TextLexer()

    code = request.content.decode('utf-8')
    if isinstance(lexer, JsonLexer):
        try:
            code = get_pretty_json(code)
        except Exception:
            return code, TextLexer()

    if isinstance(lexer, UrlEncodedLexer):
        try:
            body = {}
            for key, value in parse_qs(code).items():
                body[key] = value[0] if len(value) == 1 else value
            return get_pretty_json(body), JsonLexer()
        except Exception:
            return code, TextLexer()
    return code, lexer
