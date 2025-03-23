import json
from json import JSONDecodeError

from httpx._status_codes import codes

from httpx import Response as _Response
from rich.console import Console, ConsoleOptions, RenderResult

from ._render_response import render_request, render_response

__all__ = ("Response",)


class Response(_Response):
    """
    Extends the httpx.Response class to provide enhanced rendering in the rich console.
    This class uses the rich library's capabilities to format HTTP response objects visually
    when output to a console supporting rich text formatting.
    """

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """
        Define how this HTTP response is rendered within the rich console.

        This method customizes the rendering of httpx.Response objects in a console using the
        rich library. It adjusts the rendering width based on the console settings.

        :param console: The rich console object that is used to render this response.
        :param options: Console options that include configuration for rendering, such as width.
        :return: Yields rendered segments as part of the rich console's render process.
        """
        # Check if a specific width limit has been set. If options.min_width and options.max_width
        # are the same, then a specific width limit has been set and we use options.max_width.
        # If not, we use a large default width of 1024^2 (which practically means no width limit).
        width = options.max_width if options.min_width == options.max_width else 1024 ** 2
        if self._request:
            yield from render_request(self.request, width=width)
        yield from render_response(self, width=width)
