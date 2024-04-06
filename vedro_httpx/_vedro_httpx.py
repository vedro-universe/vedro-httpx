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

from ._request_recorder import RequestRecorder
from ._request_recorder import request_recorder as default_request_recorder

__all__ = ("VedroHTTPX", "VedroHTTPXPlugin",)


class VedroHTTPXPlugin(Plugin):
    def __init__(self, config: Type["VedroHTTPX"], *,
                 request_recorder: RequestRecorder = default_request_recorder) -> None:
        super().__init__(config)
        self._request_recorder = request_recorder
        self._save_requests = False
        self._requests_artifact_name = config.requests_artifact_name

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher.listen(ArgParseEvent, self.on_arg_parse) \
                  .listen(ArgParsedEvent, self.on_arg_parsed) \
                  .listen(ScenarioRunEvent, self.on_scenario_run) \
                  .listen(ScenarioFailedEvent, self.on_scenario_end) \
                  .listen(ScenarioPassedEvent, self.on_scenario_end)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        group = event.arg_parser.add_argument_group("VedroHttpx")
        group.add_argument("--httpx-save-requests", action="store_true",
                           default=self._save_requests, help="<message>")

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        self._save_requests = event.args.httpx_save_requests
        if self._save_requests:
            self._request_recorder.enable()

    async def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        if self._save_requests:
            self._request_recorder.reset()

    async def on_scenario_end(self,
                              event: Union[ScenarioPassedEvent, ScenarioFailedEvent]) -> None:
        if self._save_requests:
            tmp_file = create_tmp_file(suffix=".har")
            self._request_recorder.save(tmp_file)

            artifact = FileArtifact(self._requests_artifact_name, "application/json", tmp_file)
            event.scenario_result.attach(artifact)


class VedroHTTPX(PluginConfig):
    plugin = VedroHTTPXPlugin

    requests_artifact_name: str = "httpx-requests.har"
