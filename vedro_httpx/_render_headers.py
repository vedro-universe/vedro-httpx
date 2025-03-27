import os
from typing import List, Tuple

from httpx._models import Headers, Request, Response
from pygments.lexer import Lexer
from pygments.lexers import HttpLexer, TextLexer

__all__ = ("format_request_headers", "format_response_headers")

def headers_lines(headers: Headers) -> List[str]:
    lines = []
    for header in headers:
        values = headers.get_list(header)
        for value in values:
            lines.append(f"{header}: {value}")
    return lines

def format_request_headers(request: Request) -> Tuple[str, Lexer]:
    """
    Format the HTTP headers of a request and determine the appropriate lexer for syntax
    highlighting.

    :param request: The HTTP request object whose headers are to be formatted.
    :return: A tuple containing the formatted headers as a string and the corresponding
             HttpLexer instance.
    """
    lines = headers_lines(request.headers)
    return os.linesep.join(lines), TextLexer()


def format_response_headers(response: Response) -> Tuple[str, Lexer]:
    """
    Format the HTTP headers of a response and determine the appropriate lexer for syntax
    highlighting.

    :param response: The HTTP response object whose headers are to be formatted.
    :return: A tuple containing the formatted headers as a string and the corresponding
             HttpLexer instance.
    """
    lines = [f"{response.http_version} {response.status_code} {response.reason_phrase}"]
    lines.extend(headers_lines(response.headers))
    return os.linesep.join(lines), HttpLexer()
