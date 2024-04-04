from typing import List

from ._response import Response
from .har import AsyncHARFormatter, Entry, SyncHARFormatter

__all__ = ("sync_request_recorder", "SyncRequestRecorder",
           "async_request_recorder", "AsyncRequestRecorder", "BaseRequestRecorder")


class BaseRequestRecorder:
    def __init__(self) -> None:
        self._enabled: bool = False
        self._entries: List[Entry] = []

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False


class SyncRequestRecorder(BaseRequestRecorder):
    def __init__(self, formatter: SyncHARFormatter) -> None:
        super().__init__()
        self._formatter = formatter

    def record(self, response: Response) -> None:
        formatted = self._formatter.format_entry(response, response.request)
        self._entries.append(formatted)

    def reset(self) -> None:
        self._entries.clear()


class AsyncRequestRecorder(BaseRequestRecorder):
    def __init__(self, formatter: AsyncHARFormatter) -> None:
        super().__init__()
        self._formatter = formatter

    async def record(self, response: Response) -> None:
        if not self._enabled:
            return
        formatted = await self._formatter.format_entry(response, response.request)
        self._entries.append(formatted)

    async def reset(self) -> None:
        self._entries.clear()


sync_request_recorder = SyncRequestRecorder(SyncHARFormatter())
async_request_recorder = AsyncRequestRecorder(AsyncHARFormatter())
