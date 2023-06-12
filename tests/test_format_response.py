from os import linesep

from baby_steps import given, then, when
from pygments.lexers import HttpLexer

from vedro_httpx import Response
from vedro_httpx._format_response import format_response_headers


def test_format_response_no_headers():
    with given:
        response = Response(status_code=200)

    with when:
        code, lexer = format_response_headers(response)

    with then:
        assert code == "HTTP/1.1 200 OK"
        assert isinstance(lexer, HttpLexer)


def test_format_response_headers():
    with given:
        response = Response(status_code=200, headers=[
            ("Content-Type", "application/json"),
            ("Set-Cookie", "lang=en"),
            ("Set-Cookie", "country=us")
        ])

    with when:
        code, lexer = format_response_headers(response)

    with then:
        assert code == linesep.join([
            "HTTP/1.1 200 OK",
            "content-type: application/json",
            "set-cookie: lang=en",
            "set-cookie: country=us"
        ])
        assert isinstance(lexer, HttpLexer)
