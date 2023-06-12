import json
import os
from typing import Any, Tuple, Union

from httpx import Response
from pygments.lexer import Lexer
from pygments.lexers import HttpLexer, JsonLexer, get_lexer_for_mimetype
from pygments.util import ClassNotFound
from rich.console import RenderResult
from rich.syntax import Syntax

__all__ = ("format_response",)


def format_response(response: Response) -> RenderResult:
    yield "Response:"
    headers, http_lexer = format_response_headers(response)
    yield Syntax(headers, http_lexer, theme="ansi_dark")

    body, lexer = format_response_body(response)
    yield Syntax(body, lexer, theme="ansi_dark", background_color="default", indent_guides=True)


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
        lexer = ""  # type: ignore

    code = response.text
    if isinstance(lexer, JsonLexer):
        try:
            code = json.dumps(response.json(), indent=4)
        except BaseException:
            pass
    return code, lexer
