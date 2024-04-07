from argparse import ArgumentParser, Namespace
from typing import Optional, Type
from unittest.mock import Mock, call

import pytest
from baby_steps import given, then, when
from vedro import FileArtifact
from vedro.core import Dispatcher, ScenarioResult, VirtualScenario
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    ScenarioFailedEvent,
    ScenarioPassedEvent,
    ScenarioRunEvent,
    _ScenarioEvent,
)

from vedro_httpx import VedroHTTPX, VedroHTTPXPlugin
from vedro_httpx.recorder import RequestRecorder

from ._utils import request_recorder_

__all__ = ("request_recorder_",)  # fixtures


@pytest.fixture()
def dispatcher() -> Dispatcher:
    return Dispatcher()


@pytest.fixture
def httpx_plugin(dispatcher: Dispatcher, request_recorder_: RequestRecorder) -> VedroHTTPXPlugin:
    plugin = VedroHTTPXPlugin(VedroHTTPX, request_recorder=request_recorder_)
    plugin.subscribe(dispatcher)
    return plugin


def make_scenario_result() -> ScenarioResult:
    vscenario = Mock(VirtualScenario)
    return ScenarioResult(vscenario)


async def fire_arg_parsed_event(dispatcher: Dispatcher, *,
                                httpx_record_requests: Optional[bool] = None) -> None:
    arg_parse_event = ArgParseEvent(ArgumentParser())
    await dispatcher.fire(arg_parse_event)

    arg_parsed_event = ArgParsedEvent(Namespace(httpx_record_requests=httpx_record_requests))
    await dispatcher.fire(arg_parsed_event)


@pytest.mark.usefixtures(httpx_plugin.__name__)
async def test_arg_parsed_disabled(*, dispatcher: Dispatcher, request_recorder_: Mock):
    with when:
        await fire_arg_parsed_event(dispatcher)

    with then:
        assert request_recorder_.mock_calls == []


@pytest.mark.usefixtures(httpx_plugin.__name__)
async def test_arg_parsed_enabled(*, dispatcher: Dispatcher, request_recorder_: Mock):
    with when:
        await fire_arg_parsed_event(dispatcher, httpx_record_requests=True)

    with then:
        assert request_recorder_.mock_calls == [call.enable()]


@pytest.mark.usefixtures(httpx_plugin.__name__)
async def test_scenario_run_disabled(*, dispatcher: Dispatcher, request_recorder_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)
        request_recorder_.reset_mock()

        event = ScenarioRunEvent(make_scenario_result())

    with when:
        await dispatcher.fire(event)

    with then:
        assert request_recorder_.mock_calls == []


@pytest.mark.usefixtures(httpx_plugin.__name__)
async def test_scenario_run_enabled(*, dispatcher: Dispatcher, request_recorder_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, httpx_record_requests=True)
        request_recorder_.reset_mock()

        event = ScenarioRunEvent(make_scenario_result())

    with when:
        await dispatcher.fire(event)

    with then:
        assert request_recorder_.mock_calls == [call.reset()]


@pytest.mark.parametrize("event_class", [ScenarioPassedEvent, ScenarioFailedEvent])
@pytest.mark.usefixtures(httpx_plugin.__name__)
async def test_scenario_end_disabled(event_class: Type[_ScenarioEvent], *, dispatcher: Dispatcher,
                                     request_recorder_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher)
        request_recorder_.reset_mock()

        scenario_result = make_scenario_result()
        event = event_class(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert request_recorder_.mock_calls == []

        assert scenario_result.artifacts == []


@pytest.mark.parametrize("event_class", [ScenarioPassedEvent, ScenarioFailedEvent])
@pytest.mark.usefixtures(httpx_plugin.__name__)
async def test_scenario_end_enabled(event_class: Type[_ScenarioEvent], *, dispatcher: Dispatcher,
                                    request_recorder_: Mock):
    with given:
        await fire_arg_parsed_event(dispatcher, httpx_record_requests=True)
        request_recorder_.reset_mock()

        scenario_result = make_scenario_result()
        event = event_class(scenario_result)

    with when:
        await dispatcher.fire(event)

    with then:
        assert len(request_recorder_.mock_calls) == 1
        assert request_recorder_.save.assert_called_once() is None

        assert len(scenario_result.artifacts) == 1

        artifact = scenario_result.artifacts[0]
        assert isinstance(artifact, FileArtifact)
        assert artifact.name == "httpx-requests.har"
        assert artifact.mime_type == "application/json"
        assert artifact.path == request_recorder_.save.mock_calls[0].args[0]
