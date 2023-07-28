import json
import os
from typing import Any, Optional, Tuple, Union

from httpx import Response
from pygments.lexer import Lexer
from pygments.lexers import HttpLexer, JsonLexer, TextLexer, get_lexer_for_mimetype
from pygments.util import ClassNotFound
from rich.console import RenderResult
from rich.syntax import Syntax

__all__ = ("render_response",)


def render_response(response: Response, *,
                    theme: str = "ansi_dark", width: Optional[int] = None) -> RenderResult:
    yield "Response:"
    headers, http_lexer = format_response_headers(response)
    yield Syntax(headers, http_lexer, theme=theme, word_wrap=True, code_width=width)

    body, lexer = format_response_body(response)
    yield Syntax(body, lexer,
                 theme=theme, word_wrap=True, indent_guides=True, code_width=width)


def format_response_headers(response: Response) -> Tuple[str, Lexer]:
    lines = [f"{response.http_version} {response.status_code} {response.reason_phrase}"]
    for header in response.headers:
        values = response.headers.get_list(header)
        for value in values:
            lines.append(f"{header}: {value}")

    return os.linesep.join(lines), HttpLexer()


def format_response_body(response: Response) -> Tuple[Any, Union[Lexer, str]]:
    content_type = response.headers.get("Content-Type", "")
    mime_type, *_ = content_type.split(";")
    try:
        lexer = get_lexer_for_mimetype(mime_type.strip())
    except ClassNotFound:
        preview = response.content[:10]
        return f"<binary preview={preview!r} len={len(response.content)}>", ""

    code = response.text
    if isinstance(lexer, JsonLexer):
        try:
            code = json.dumps(response.json(), indent=4)
        except BaseException:
            return code, TextLexer()
    return code, lexer
