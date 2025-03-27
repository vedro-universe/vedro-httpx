import json
from typing import Any, Optional, Tuple, Union

import rich
from httpx import Response
from pygments.lexer import Lexer
from pygments.lexers import JsonLexer, TextLexer, get_lexer_for_mimetype
from pygments.util import ClassNotFound
from rich.console import RenderResult
from rich.syntax import Syntax

__all__ = ("render_response")

from vedro_httpx._render_headers import format_response_headers


def render_response(response: Response, *,
                    theme: str = "ansi_dark", width: Optional[int] = None) -> RenderResult:
    """
    Yield formatted sections of an HTTP response for rendering in a rich console.

    This function creates visually appealing and structured representations of HTTP response
    headers and body using syntax highlighting. It automatically selects appropriate lexers for
    different content types and applies themes and formatting options.

    :param response: The HTTP response object from httpx to render.
    :param theme: The color theme to use for syntax highlighting (default 'ansi_dark').
    :param width: The maximum width for the code blocks. If not set, defaults to console width.
    :return: Yields formatted rich syntax objects for headers and body.
    """
    yield "← Response"
    headers, http_lexer = format_response_headers(response)
    yield Syntax(headers, http_lexer, theme=theme, word_wrap=True, code_width=width)

    body, lexer = format_response_body(response)
    yield Syntax(body, lexer,
                 theme=theme, word_wrap=True, indent_guides=True, code_width=width)


def format_response_body(response: Response) -> Tuple[Any, Union[Lexer, str]]:
    """
    Format the body of an HTTP response and select an appropriate lexer for syntax highlighting.

    This function handles various content types intelligently, using a JSON lexer for JSON content
    to improve formatting, and defaulting to plain text or binary previews for unsupported types.

    :param response: The HTTP response object whose body is to be formatted.
    :return: A tuple containing the formatted body as a string (or a placeholder for binary data)
             and the lexer to use for syntax highlighting, or an empty string if no suitable
             lexer is found.
    """
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
            code = json.dumps(response.json(), indent=4, ensure_ascii=False)
        except Exception:
            return code, TextLexer()
    return code, lexer
