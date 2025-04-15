from os import linesep

import pytest
from baby_steps import given, then, when
from httpx import Request
from httpx._client import BaseClient
from pygments.lexers import HttpLexer, JsonLexer, TextLexer, UrlEncodedLexer
from rich.syntax import Syntax

from vedro_httpx import Response
from vedro_httpx._response_renderer import ResponseRenderer


@pytest.fixture()
def response_renderer() -> ResponseRenderer:
    return ResponseRenderer(include_request_body=True)


def test_format_response_no_headers(response_renderer):
    with given:
        response = Response(status_code=200)

    with when:
        code, lexer = response_renderer._format_response_headers(response)

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
        code, lexer = response_renderer._format_response_headers(response)

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
        code, lexer = response_renderer._format_response_body(response)

    with then:
        assert code == "<binary preview=b'' len=0>"
        assert isinstance(lexer, TextLexer)


def test_format_response_no_content_type(response_renderer):
    with given:
        body = b"a04e8431ff62"
        response = Response(status_code=200, content=body)

    with when:
        code, lexer = response_renderer._format_response_body(response)

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
        code, lexer = response_renderer._format_response_body(response)

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
        code, lexer = response_renderer._format_response_body(response)

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
        code, lexer = response_renderer._format_response_body(response)

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
        res = response_renderer._render_response(response)

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


def test_render_response_with_get_request(response_renderer):
    with given:
        request = Request(
            method='GET',
            url='http://get_url.com',
            params={'test': 1},
            headers={'User-Agent': 'pytest'},
        )

    with when:
        res = response_renderer._render_request(request)

    with then:
        text, headers_syntax = list(res)

        assert text == "→ Request"
        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "GET http://get_url.com?test=1 HTTP/1.1",
            "host: get_url.com",
            "user-agent: pytest",
        ])


def test_render_response_with_post_request_json(response_renderer):
    with given:
        request = Request(
            method='POST',
            url='http://get_url.com',
            params={'test': 1},
            headers={'User-Agent': 'pytest', 'Content-Type': 'application/json'},
            json={'id': 1}
        )

    with when:
        res = response_renderer._render_request(request)

    with then:
        text, headers_syntax, body_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "POST http://get_url.com?test=1 HTTP/1.1",
            "host: get_url.com",
            "user-agent: pytest",
            "content-type: application/json",
            "content-length: 8"
        ])

        assert isinstance(body_syntax, Syntax)
        assert body_syntax.code == '{\n    "id": 1\n}'
        assert isinstance(body_syntax.lexer, JsonLexer)


def test_render_response_with_patch_request_form_urlencoded(response_renderer):
    with given:
        request = BaseClient().build_request(
            method='PATCH',
            url='http://get_url.com',
            params={'test': 1},
            headers={'User-Agent': 'pytest'},
            data={'id': 1, 'name': 'TestName'}
        )

    with when:
        res = response_renderer._render_request(request)

    with then:
        text, headers_syntax, body_syntax = list(res)

        assert text == "→ Request"

        assert isinstance(headers_syntax, Syntax)
        assert headers_syntax.code == linesep.join([
            "PATCH http://get_url.com?test=1 HTTP/1.1",
            "host: get_url.com",
            "accept: */*",
            "accept-encoding: gzip, deflate",
            "connection: keep-alive",
            "user-agent: pytest",
            "content-length: 18",
            "content-type: application/x-www-form-urlencoded",
        ])

        assert isinstance(body_syntax, Syntax)
        assert body_syntax.code == 'id=1&\nname=TestName'
        assert isinstance(body_syntax.lexer, UrlEncodedLexer)
