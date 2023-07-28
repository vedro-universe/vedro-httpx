import json
from io import StringIO
from os import linesep

import pytest
from baby_steps import given, then, when
from rich.console import Console
from vedro.plugins.director.rich._rich_printer import make_console

from vedro_httpx import Response


@pytest.fixture()
def buffer() -> StringIO:
    return StringIO()


@pytest.fixture()
def console(buffer: StringIO) -> Console:
    console = make_console()
    console.file = buffer
    return console


def test_render_response_console(*, console: Console, buffer: StringIO):
    with given:
        header_val, body_val = "x" * 100, "y" * 100
        response = Response(
            status_code=200,
            content=json.dumps({
                "id": 1,
                "name": body_val
            }),
            headers={
                "Content-Type": "application/json",
                "X-Token": header_val
            }
        )

    with when:
        console.print(response)

    with then:
        assert buffer.getvalue() == linesep.join([
            'Response:',
            '[94mHTTP[0m/[94m1.1[0m [94m200[0m [96mOK[0m',
            '[96mcontent-type[0m: application/json',
            f'[96mx-token[0m: {header_val}',
            '[96mcontent-length[0m: 121',
            '{',
            '[2;90m│   [0m[94m"id"[0m:[90m [0m[94m1[0m,',
            f'[2;90m│   [0m[94m"name"[0m:[90m [0m[33m"{body_val}"[0m',
            '}',
            '',
        ])


def test_render_response_console_width(*, console: Console, buffer: StringIO):
    with given:
        width = 80
        header_val, body_val = "x" * 100, "y" * 100
        response = Response(
            status_code=200,
            content=json.dumps({
                "id": 1,
                "name": body_val
            }),
            headers={
                "Content-Type": "application/json",
                "X-Token": header_val
            }
        )

    with when:
        console.print(response, width=width, overflow="ellipsis", no_wrap=True)

    with then:
        buffer_value = buffer.getvalue()
        output = linesep.join(x.rstrip(" ") for x in buffer_value.splitlines())

        header_len = width - len("x-token: ") - 1
        body_len = width - len('│   "name": "') - 1

        assert output == linesep.join([
            'Response:',
            '[94mHTTP[0m/[94m1.1[0m [94m200[0m [96mOK[0m',
            '[96mcontent-type[0m: application/json',
            f'[96mx-token[0m: {header_val[:header_len]}…',
            '[96mcontent-length[0m: 121',
            '{',
            '[2;90m│   [0m[94m"id"[0m:[90m [0m[94m1[0m,',
            '[2;90m│   [0m[94m"name"[0m:'
            f'[90m [0m[33m"{body_val[:body_len]}…[0m',
            '}',
        ])
