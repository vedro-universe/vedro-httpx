from httpx import Response as _Response
from rich.console import Console, ConsoleOptions, RenderResult

from ._response_renderer import ResponseRenderer

__all__ = ("Response",)


class Response(_Response):
    """
    Extends the httpx.Response class to provide enhanced rendering in the rich console.
    This class uses the rich library's capabilities to format HTTP response objects visually
    when output to a console supporting rich text formatting.
    """

    # Default renderer (can be overridden at runtime)
    __rich_renderer__: ResponseRenderer = ResponseRenderer()

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """
        Define how this HTTP response is rendered within the rich console.

        This method customizes the rendering of httpx.Response objects in a console using the
        rich library. It adjusts the rendering width based on the console settings.

        :param console: The rich console object that is used to render this response.
        :param options: Console options that include configuration for rendering, such as width.
        :return: Yields rendered segments as part of the rich console's render process.
        """
        yield from self.__rich_renderer__.render(self, width=options.max_width)
