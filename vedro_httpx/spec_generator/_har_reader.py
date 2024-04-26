import json
import os
from typing import Generator, List, cast

import vedro_httpx.recorder.har as har

__all__ = ("HARReader",)


class HARReader:
    def __init__(self, directory: str) -> None:
        self.directory = directory

    def _find_har_file_paths(self) -> Generator[str, None, None]:
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith(".har"):
                    yield os.path.join(root, file)

    def _read_har_file(self, file_path: str) -> har.HAR:
        with open(file_path) as file:
            return cast(har.HAR, json.load(file))

    def get_entries(self) -> List[har.Entry]:
        entries = []
        for file_path in self._find_har_file_paths():
            har = self._read_har_file(file_path)
            entries.extend(har["log"]["entries"])
        return entries
