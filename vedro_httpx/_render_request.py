import json
from typing import Any, Optional, Tuple, Union

from httpx._models import Request
from pygments.lexer import Lexer
from pygments.lexers import JsonLexer, TextLexer, UrlEncodedLexer, get_lexer_for_mimetype
from pygments.util import ClassNotFound
from rich.console import RenderResult
from rich.syntax import Syntax

__all__ = ( "render_request")

from vedro_httpx._render_headers import format_request_headers


def render_request(request: Request, *,
                   theme: str = "ansi_dark", width: Optional[int] = None) -> RenderResult:
    yield f"\n→ Request {request.method} {request.url}"
    headers, http_lexer = format_request_headers(request)
    yield Syntax(headers, http_lexer, theme=theme, word_wrap=True, code_width=width)

    body, lexer = format_request_body(request)
    if body is not None:
        yield Syntax(body, lexer, theme=theme, word_wrap=True, code_width=width)



def format_request_body(request: Request) -> Tuple[Any, Union[Lexer, str]]:
    content_type = request.headers.get("Content-Type", "")
    mime_type, *_ = content_type.split(";")

    if content_type == "" or mime_type == 'multipart/form-data':
        return None, ""

    try:
        lexer = get_lexer_for_mimetype(mime_type.strip())
    except ClassNotFound:
        preview = request.content[:10]
        return f"<binary preview={preview!r} len={len(request.content)}>", ""

    code = request.content.decode('utf-8')
    if isinstance(lexer, JsonLexer):
        try:
            code = json.dumps(request.content.decode('utf-8'), indent=4)
        except Exception:
            return code, TextLexer()

    if isinstance(lexer, UrlEncodedLexer):
        if isinstance(lexer, UrlEncodedLexer):
            body = request.content.decode('utf-8').replace('&', '\n&')
            return body, TextLexer()
    return code, lexer
