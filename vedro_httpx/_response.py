from httpx import Response as _Response
from rich.console import Console, ConsoleOptions, RenderResult

from ._render_response import render_response

__all__ = ("Response",)


class Response(_Response):
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield from render_response(self)
