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

__all__ = ("VedroHTTPX", "VedroHTTPXPlugin",)


class VedroHTTPXPlugin(Plugin):
    def __init__(self, config: Type["VedroHTTPX"], *,
                 request_recorder: RequestRecorder = default_request_recorder) -> None:
        super().__init__(config)
        self._request_recorder = request_recorder
        self._record_requests = config.record_requests
        self._requests_artifact_name = config.requests_artifact_name

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher.listen(ArgParseEvent, self.on_arg_parse) \
                  .listen(ArgParsedEvent, self.on_arg_parsed) \
                  .listen(ScenarioRunEvent, self.on_scenario_run) \
                  .listen(ScenarioFailedEvent, self.on_scenario_end) \
                  .listen(ScenarioPassedEvent, self.on_scenario_end)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        group = event.arg_parser.add_argument_group("VedroHttpx")
        help_message = ("Enable recording of HTTP requests made during scenario execution. "
                        "Recorded data will be saved as a scenario artifact in HAR format.")
        group.add_argument("--httpx-record-requests", action="store_true",
                           default=self._record_requests, help=help_message)

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        self._record_requests = event.args.httpx_record_requests
        if self._record_requests:
            self._request_recorder.enable()

    async def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        if self._record_requests:
            self._request_recorder.reset()

    async def on_scenario_end(self,
                              event: Union[ScenarioPassedEvent, ScenarioFailedEvent]) -> None:
        if self._record_requests:
            tmp_file = create_tmp_file(suffix=".har")
            self._request_recorder.save(tmp_file)

            artifact = FileArtifact(self._requests_artifact_name, "application/json", tmp_file)
            event.scenario_result.attach(artifact)


class VedroHTTPX(PluginConfig):
    plugin = VedroHTTPXPlugin

    # Enable recording of HTTP requests
    # When enabled, the plugin records HTTP requests made during scenario execution
    # and saves the data as a scenario artifact in HAR format
    record_requests: bool = False

    # Artifact file name for recorded HTTP requests
    requests_artifact_name: str = "httpx-requests.har"
