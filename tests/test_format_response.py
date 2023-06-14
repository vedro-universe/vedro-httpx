from os import linesep

from baby_steps import given, then, when
from pygments.lexers import HttpLexer, JsonLexer, TextLexer
from rich.syntax import Syntax

from vedro_httpx import Response
from vedro_httpx._render_response import (
    format_response_body,
    format_response_headers,
    render_response,
)


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


def test_format_response_no_body():
    with given:
        response = Response(status_code=200)

    with when:
        code, lexer = format_response_body(response)

    with then:
        assert code == "<binary preview=b'' len=0>"
        assert lexer == ""


def test_format_response_no_content_type():
    with given:
        body = b"a04e8431ff62"
        response = Response(status_code=200, content=body)

    with when:
        code, lexer = format_response_body(response)

    with then:
        assert code == f"<binary preview={body[:10]} len={len(body)}>"
        assert lexer == ""


def test_format_response_text():
    with given:
        body = b"Hello, world!"
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "text/plain"
        })

    with when:
        code, lexer = format_response_body(response)

    with then:
        assert code == "Hello, world!"
        assert isinstance(lexer, TextLexer)


def test_format_response_json():
    with given:
        body = b'{"id": 1}'
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "application/json"
        })

    with when:
        code, lexer = format_response_body(response)

    with then:
        assert code == '{\n    "id": 1\n}'
        assert isinstance(lexer, JsonLexer)


def test_format_response_invalid_json():
    with given:
        body = b'{"id"}'
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "application/json"
        })

    with when:
        code, lexer = format_response_body(response)

    with then:
        assert code == '{"id"}'
        assert isinstance(lexer, TextLexer)


def test_render_response():
    with given:
        body = b'{"id": 1}'
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "application/json"
        })

    with when:
        res = render_response(response)

    with then:
        text, http_syntax, json_syntax = list(res)
        assert text == "Response:"

        assert isinstance(http_syntax, Syntax)
        assert http_syntax.code == linesep.join([
            "HTTP/1.1 200 OK",
            "content-type: application/json",
            "content-length: 9",
        ])
        assert isinstance(http_syntax.lexer, HttpLexer)

        assert isinstance(json_syntax, Syntax)
        assert json_syntax.code == '{\n    "id": 1\n}'
        assert isinstance(json_syntax.lexer, JsonLexer)
