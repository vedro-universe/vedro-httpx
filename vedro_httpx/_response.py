from httpx import Response as _Response
from rich.console import Console, ConsoleOptions, RenderResult

from ._render_response import render_response

__all__ = ("Response",)


class Response(_Response):
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # Check if a specific width limit has been set. If options.min_width and options.max_width
        # are the same, then a specific width limit has been set and we use options.max_width.
        # If not, we use a large default width of 1024^2 (which practically means no width limit).
        width = options.max_width if options.min_width == options.max_width else 1024 ** 2
        yield from render_response(self, width=width)
