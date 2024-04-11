import json
from pathlib import Path
from typing import List

from .._response import Response
from .._version import version as vedro_httpx_version
from ._async_har_formatter import AsyncHARFormatter
from ._har_builder import HARBuilder
from ._sync_har_formatter import SyncHARFormatter
from .har import Entry

__all__ = ("request_recorder", "RequestRecorder",)


class RequestRecorder:
    """
    Manages the recording of HTTP request and response pairs into HAR (HTTP Archive) format.
    This recorder supports both synchronous and asynchronous operations.
    """

    def __init__(self, har_builder: HARBuilder,
                 sync_har_formatter: SyncHARFormatter,
                 async_har_formatter: AsyncHARFormatter) -> None:
        """
        Initializes the request recorder with necessary HAR formatting tools.

        :param har_builder: The HARBuilder to use for creating HAR objects.
        :param sync_har_formatter: The synchronous HAR formatter.
        :param async_har_formatter: The asynchronous HAR formatter.
        """
        self._har_builder = har_builder
        self._sync_formatter = sync_har_formatter
        self._async_formatter = async_har_formatter
        self._enabled: bool = False
        self._entries: List[Entry] = []

    def enable(self) -> None:
        """
        Enable the recording of HTTP transactions.
        """
        self._enabled = True

    def disable(self) -> None:
        """
        Disable the recording of HTTP transactions.
        """
        self._enabled = False

    def is_enabled(self) -> bool:
        """
        Check if the recording is currently enabled.

        :return: True if recording is enabled, otherwise False.
        """
        return self._enabled

    async def async_record(self, response: Response) -> None:
        """
        Record an HTTP transaction if recording is enabled.

        :param response: The HTTP Response object to record.
        """
        if self._enabled:
            formatted = await self._async_formatter.format_entry(response, response.request)
            self._entries.append(formatted)

    def sync_record(self, response: Response) -> None:
        """
        Record an HTTP transaction if recording is enabled.

        :param response: The HTTP Response object to record.
        """
        if self._enabled:
            formatted = self._sync_formatter.format_entry(response, response.request)
            self._entries.append(formatted)

    def reset(self) -> None:
        """
        Reset the recorded entries.
        """
        self._entries.clear()

    def save(self, file_path: Path) -> None:
        """
        Save the recorded entries to a file in HAR format.

        :param file_path: The path to the file where the HAR data will be saved.
        """
        log = self._har_builder.build_log(self._entries)
        har = self._har_builder.build_har(log)
        file_path.write_text(json.dumps(har, indent=2, ensure_ascii=False))


_har_builder = HARBuilder("vedro-httpx", vedro_httpx_version)
request_recorder = RequestRecorder(
    har_builder=_har_builder,
    sync_har_formatter=SyncHARFormatter(_har_builder),
    async_har_formatter=AsyncHARFormatter(_har_builder)
)
