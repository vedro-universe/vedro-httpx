import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from baby_steps import given, then, when

from vedro_httpx import RequestRecorder
from vedro_httpx import __version__ as vedro_httpx_version
from vedro_httpx.har import AsyncHARFormatter, HARBuilder, SyncHARFormatter

from ._utils import async_formatter, builder, request_recorder, sync_formatter

__all__ = ("builder", "sync_formatter", "async_formatter", "request_recorder",)  # fixtures


@pytest.fixture
def sync_formatter_() -> SyncHARFormatter:
    return Mock()


@pytest.fixture
def async_formatter_() -> AsyncHARFormatter:
    return AsyncMock()


def test_disabled_by_default(*, request_recorder: RequestRecorder):
    with given:
        pass

    with when:
        is_enabled = request_recorder.is_enabled()

    with then:
        assert not is_enabled


def test_enable(*, request_recorder: RequestRecorder):
    with when:
        request_recorder.enable()

    with then:
        assert request_recorder.is_enabled()


def test_disable(*, request_recorder: RequestRecorder):
    with given:
        request_recorder.enable()

    with when:
        request_recorder.disable()

    with then:
        assert not request_recorder.is_enabled()


def test_record_sync_enabled(*, builder: HARBuilder, sync_formatter_: Mock,
                             async_formatter_: Mock):
    with given:
        request_recorder = RequestRecorder(builder, sync_formatter_, async_formatter_)

        request_recorder.enable()

    with when:
        request_recorder.sync_record(response=MagicMock())

    with then:
        assert sync_formatter_.format_entry.assert_called_once() is None
        assert async_formatter_.format_entry.assert_not_called() is None


def test_record_sync_disabled(*, builder: HARBuilder, sync_formatter_: Mock,
                              async_formatter_: Mock):
    with given:
        request_recorder = RequestRecorder(builder, sync_formatter_, async_formatter_)

    with when:
        request_recorder.sync_record(response=MagicMock())

    with then:
        assert sync_formatter_.format_entry.assert_not_called() is None
        assert async_formatter_.format_entry.assert_not_called() is None


async def test_record_async_enabled(*, builder: HARBuilder, sync_formatter_: Mock,
                                    async_formatter_: Mock):
    with given:
        request_recorder = RequestRecorder(builder, sync_formatter_, async_formatter_)

        request_recorder.enable()

    with when:
        await request_recorder.async_record(response=MagicMock())

    with then:
        assert async_formatter_.format_entry.assert_called_once() is None
        assert sync_formatter_.format_entry.assert_not_called() is None


async def test_record_async_disabled(*, builder: HARBuilder, sync_formatter_: Mock,
                                     async_formatter_: Mock):
    with given:
        request_recorder = RequestRecorder(builder, sync_formatter_, async_formatter_)

    with when:
        await request_recorder.async_record(response=MagicMock())

    with then:
        assert async_formatter_.format_entry.assert_not_called() is None
        assert sync_formatter_.format_entry.assert_not_called() is None


def test_save_requests(*, request_recorder: RequestRecorder, tmp_path: Path):
    with given:
        file_path = tmp_path / "requests.har"

    with when:
        request_recorder.save(file_path)

    with then:
        har = json.loads(file_path.read_text())
        assert har == {
            "log": {
                "version": "1.2",
                "creator": {
                    "name": "vedro-httpx",
                    "version": vedro_httpx_version
                },
                "entries": [],
                "pages": []
            }
        }
