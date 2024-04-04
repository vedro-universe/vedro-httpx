import json
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

from ._request_recorder import AsyncRequestRecorder, SyncRequestRecorder
from ._request_recorder import async_request_recorder as async_request_recorder_
from ._request_recorder import sync_request_recorder as sync_request_recorder_

__all__ = ("VedroHTTPX", "VedroHTTPXPlugin",)


class VedroHTTPXPlugin(Plugin):
    def __init__(self, config: Type["VedroHTTPX"], *,
                 sync_request_recorder: SyncRequestRecorder = sync_request_recorder_,
                 async_request_recorder: AsyncRequestRecorder = async_request_recorder_) -> None:
        super().__init__(config)
        self._sync_request_recorder = sync_request_recorder
        self._async_request_recorder = async_request_recorder
        self._save_requests: bool = False

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
            self._sync_request_recorder.enable()
            self._async_request_recorder.enable()

    async def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        if self._save_requests:
            self._sync_request_recorder.reset()
            await self._async_request_recorder.reset()

    def _create_har(self,
                    request_recorder: Union[SyncRequestRecorder, AsyncRequestRecorder]) -> str:
        formatter = request_recorder._formatter

        creator = formatter.builder.build_creator(formatter._creator_name,
                                                  formatter._creator_version)
        log = formatter.builder.build_log(creator, request_recorder._entries)
        har = formatter.builder.build_har(log)

        return json.dumps(har, indent=2, ensure_ascii=False)

    async def on_scenario_end(self,
                              event: Union[ScenarioPassedEvent, ScenarioFailedEvent]) -> None:
        if not self._save_requests:
            return

        if self._sync_request_recorder._entries:
            tmp_file = create_tmp_file(suffix=".har")
            tmp_file.write_text(self._create_har(self._sync_request_recorder))
            artifact = FileArtifact(name="httpx-sync-requests.har",
                                    mime_type="application/json", path=tmp_file)
            event.scenario_result.attach(artifact)

        if self._async_request_recorder._entries:
            tmp_file = create_tmp_file(suffix=".har")
            tmp_file.write_text(self._create_har(self._async_request_recorder))
            artifact = FileArtifact(name="httpx-async-requests.har",
                                    mime_type="application/json", path=tmp_file)
            event.scenario_result.attach(artifact)


class VedroHTTPX(PluginConfig):
    plugin = VedroHTTPXPlugin
