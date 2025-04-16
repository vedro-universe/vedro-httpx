from typing import Type, Union

from vedro import FileArtifact, create_tmp_file
from vedro.core import Dispatcher, Plugin, PluginConfig
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    ScenarioFailedEvent,
    ScenarioPassedEvent,
    ScenarioRunEvent,
)

from vedro_httpx.recorder import RequestRecorder
from vedro_httpx.recorder import request_recorder as default_request_recorder

from ._response import Response
from ._response_renderer import ResponseRenderer

__all__ = ("VedroHTTPX", "VedroHTTPXPlugin",)


class VedroHTTPXPlugin(Plugin):
    """
    Captures and records HTTPX request data during scenario execution.

    This plugin integrates with Vedro to record outgoing HTTP requests using the httpx library.
    It saves captured traffic in HAR format as a scenario artifact. Additionally, it configures
    a custom response renderer to improve how HTTP responses are displayed in the console.
    """

    def __init__(self, config: Type["VedroHTTPX"], *,
                 request_recorder: RequestRecorder = default_request_recorder) -> None:
        """
        Initialize the VedroHTTPXPlugin with configuration and request recorder.

        :param config: The plugin configuration object.
        :param request_recorder: The recorder used to capture HTTP requests.
                                 Defaults to the shared recorder.
        """
        super().__init__(config)
        self._request_recorder = request_recorder
        self._record_requests = config.record_requests
        self._requests_artifact_name = config.requests_artifact_name
        self._response_renderer = config.response_renderer

    def subscribe(self, dispatcher: Dispatcher) -> None:
        """
        Subscribe to Vedro lifecycle events to hook into argument parsing and scenario handling.

        :param dispatcher: The event dispatcher used to bind to lifecycle events.
        """
        dispatcher.listen(ArgParseEvent, self.on_arg_parse) \
                  .listen(ArgParsedEvent, self.on_arg_parsed) \
                  .listen(ScenarioRunEvent, self.on_scenario_run) \
                  .listen(ScenarioFailedEvent, self.on_scenario_end) \
                  .listen(ScenarioPassedEvent, self.on_scenario_end)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        """
        Add custom CLI argument to control HTTP request recording.

        :param event: The event containing the argument parser to modify.
        """
        group = event.arg_parser.add_argument_group("VedroHttpx")
        help_message = ("Enable recording of HTTP requests made during scenario execution. "
                        "Recorded data will be saved as a scenario artifact in HAR format.")
        group.add_argument("--httpx-record-requests", action="store_true",
                           default=self._record_requests, help=help_message)

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        """
        Enable request recording and set response renderer after parsing CLI arguments.

        :param event: The event containing parsed arguments.
        :raises TypeError: If the response_renderer is not an instance of ResponseRenderer.
        """
        self._record_requests = event.args.httpx_record_requests
        if self._record_requests:
            self._request_recorder.enable()

        if not isinstance(self._response_renderer, ResponseRenderer):
            raise TypeError("response_renderer must be an instance of ResponseRenderer")
        setattr(Response, "__rich_renderer__", self._response_renderer)

    async def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        """
        Reset the request recorder at the start of each scenario if recording is enabled.

        :param event: The event triggered when a scenario starts running.
        """
        if self._record_requests:
            self._request_recorder.reset()

    async def on_scenario_end(self,
                              event: Union[ScenarioPassedEvent, ScenarioFailedEvent]) -> None:
        """
        Save recorded HTTP requests as a HAR file and attach them to the scenario result.

        :param event: The event triggered when a scenario finishes.
        """
        if self._record_requests:
            tmp_file = create_tmp_file(suffix=".har")
            self._request_recorder.save(tmp_file)

            artifact = FileArtifact(self._requests_artifact_name, "application/json", tmp_file)
            event.scenario_result.attach(artifact)


class VedroHTTPX(PluginConfig):
    """
    Provides configuration for the VedroHTTPXPlugin.

    This config class allows enabling HTTP request recording, customizing the
    artifact file name, and specifying the response renderer used for displaying
    HTTP responses in the console.
    """
    plugin = VedroHTTPXPlugin

    record_requests: bool = False
    """Enable recording of HTTP requests.
    When set to *True*, every HTTP request made during a scenario is captured and
    stored as a HAR file attached to the scenario results.
    """

    requests_artifact_name: str = "httpx-requests.har"
    """File name to use for the HAR artifact that stores recorded HTTP traffic."""

    response_renderer: ResponseRenderer = ResponseRenderer(
        include_request=False,
        include_request_body=False,
        include_response_body=True,
        body_binary_preview_size=10,
        body_json_indent=4,
        body_max_length=4_096,
        syntax_theme="ansi_dark",
    )
    """Pretty‑printer instance responsible for rendering httpx request/response
    objects when they are displayed in the console.
    """
