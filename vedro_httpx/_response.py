from httpx import Response as _Response
from rich.console import Console, ConsoleOptions, RenderResult

from ._format_response import format_response

__all__ = ("Response",)


class Response(_Response):
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield from format_response(self)
