import json
from os import linesep

import pytest
from baby_steps import given, then, when
from httpx import Request
from pygments.lexers import HttpLexer, JsonLexer, TextLexer, UrlEncodedLexer
from rich.syntax import Syntax

from vedro_httpx import Response, ResponseRenderer


@pytest.fixture()
def response_renderer() -> ResponseRenderer:
    return ResponseRenderer(
        include_request=True,
        include_request_body=True,
    )


# Render Response


def test_format_response_no_headers(response_renderer):
    with given:
        response = Response(status_code=200)

    with when:
        code, lexer = response_renderer.format_response_headers(response)

    with then:
        assert code == "HTTP/1.1 200 OK"
        assert isinstance(lexer, HttpLexer)


def test_format_response_headers(response_renderer):
    with given:
        response = Response(status_code=200, headers=[
            ("Content-Type", "application/json"),
            ("Set-Cookie", "lang=en"),
            ("Set-Cookie", "country=us")
        ])

    with when:
        code, lexer = response_renderer.format_response_headers(response)

    with then:
        assert code == linesep.join([
            "HTTP/1.1 200 OK",
            "content-type: application/json",
            "set-cookie: lang=en",
            "set-cookie: country=us"
        ])
        assert isinstance(lexer, HttpLexer)


def test_format_response_no_body(response_renderer):
    with given:
        response = Response(status_code=200)

    with when:
        code, lexer = response_renderer.format_response_body(response)

    with then:
        assert code == "<binary preview=b'' len=0>"
        assert isinstance(lexer, TextLexer)


def test_format_response_no_content_type(response_renderer):
    with given:
        body = b"a04e8431ff62"
        response = Response(status_code=200, content=body)

    with when:
        code, lexer = response_renderer.format_response_body(response)

    with then:
        assert code == f"<binary preview={body[:10]} len={len(body)}>"
        assert isinstance(lexer, TextLexer)


def test_format_response_text(response_renderer):
    with given:
        body = b"Hello, world!"
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "text/plain"
        })

    with when:
        code, lexer = response_renderer.format_response_body(response)

    with then:
        assert code == "Hello, world!"
        assert isinstance(lexer, TextLexer)


def test_format_response_json(response_renderer):
    with given:
        body = b'{"id": 1}'
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "application/json"
        })

    with when:
        code, lexer = response_renderer.format_response_body(response)

    with then:
        assert code == '{\n    "id": 1\n}'
        assert isinstance(lexer, JsonLexer)


def test_format_response_invalid_json(response_renderer):
    with given:
        body = b'{"id"}'
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "application/json"
        })

    with when:
        code, lexer = response_renderer.format_response_body(response)

    with then:
        assert code == '{"id"}'
        assert isinstance(lexer, TextLexer)


def test_render_response(response_renderer):
    with given:
        body = b'{"id": 1}'
        response = Response(status_code=200, content=body, headers={
            "Content-Type": "application/json"
        })

    with when:
        res = response_renderer.render_response(response)

    with then:
        text, http_syntax, json_syntax = list(res)
        assert text == "← Response"

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


# Render Request


def test_render_request_get_with_params_and_headers(response_renderer):
    with given:
        request = Request(
            method="GET",
            url="http://localhost:8000/search",
            params=[
                ("q", "test"),
                ("category", "books"),
                ("category", "electronics"),
            ],
            headers=[
                ("X-Trace-Id", "test"),
                ("Accept", "text/html"),
                ("Accept", "text/plain"),
            ],
        )

    with when:
        res = response_renderer.render_request(request)

    with then:
        text, headers_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "GET http://localhost:8000/search?q=test&category=books&category=electronics HTTP/1.1",
            "host: localhost:8000",
            "x-trace-id: test",
            "accept: text/html",
            "accept: text/plain",
        ])


def test_render_request_post_no_body(response_renderer):
    with given:
        request = Request(
            method="POST",
            url="http://localhost:8000",
        )

    with when:
        res = response_renderer.render_request(request)

    with then:
        text, headers_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "POST http://localhost:8000 HTTP/1.1",
            "host: localhost:8000",
            "content-length: 0",
        ])


def test_render_request_post_binary_body(response_renderer):
    with given:
        body = b"Hello, world!"
        request = Request(
            method="POST",
            url="http://localhost:8000",
            content=body,
        )

    with when:
        res = response_renderer.render_request(request)

    with then:
        text, headers_syntax, binary_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "POST http://localhost:8000 HTTP/1.1",
            "host: localhost:8000",
            "content-length: 13",
        ])

        assert isinstance(binary_syntax, Syntax)
        assert binary_syntax.code == f"<binary preview={body[:10]} len={len(body)}>"


def test_render_request_post_json_body(response_renderer):
    with given:
        body = {"id": 1}
        request = Request(
            method="POST",
            url="http://localhost:8000",
            json=body,
        )

    with when:
        res = response_renderer.render_request(request)

    with then:
        text, headers_syntax, json_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "POST http://localhost:8000 HTTP/1.1",
            "host: localhost:8000",
            "content-length: 8",
            "content-type: application/json",
        ])

        assert isinstance(json_syntax, Syntax)
        assert isinstance(json_syntax.lexer, JsonLexer)
        assert json_syntax.code == json.dumps(body, indent=4)


def test_render_request_post_urlencoded_body(response_renderer):
    with given:
        body = {
            "username": "test",
            "tag": ["test1", "test2"],
        }
        request = Request(
            method="POST",
            url="http://localhost:8000",
            data=body,
        )

    with when:
        res = response_renderer.render_request(request)

    with then:
        text, headers_syntax, urlencoded_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "POST http://localhost:8000 HTTP/1.1",
            "host: localhost:8000",
            "content-length: 33",
            "content-type: application/x-www-form-urlencoded",
        ])

        assert isinstance(urlencoded_syntax, Syntax)
        assert isinstance(urlencoded_syntax.lexer, UrlEncodedLexer)
        assert urlencoded_syntax.code == linesep.join([
            "username=test&",
            "tag=test1&",
            "tag=test2",
        ])
