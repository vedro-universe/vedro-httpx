from typing import Generator

import httpx
from baby_steps import given, then, when
from rich.console import Console
from rich.syntax import Syntax

from vedro_httpx import Response


def test_response():
    with when:
        response = Response(status_code=200)

    with then:
        assert isinstance(response, httpx.Response)


def test_response_rich():
    with given:
        response = Response(status_code=200)
        console = Console()

    with when:
        res = response.__rich_console__(console, console.options)

    with then:
        assert isinstance(res, Generator)
        assert all(isinstance(x, (str, Syntax)) for x in res)
