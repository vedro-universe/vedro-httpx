import json
import os
from typing import Generator, List, cast

import vedro_httpx.recorder.har as har

__all__ = ("HARReader",)


class HARReader:
    """
    Reads HAR (HTTP Archive) files from a directory.

    This class provides methods to search for HAR files in a specified directory,
    read their contents, and extract HTTP request and response entries.
    """

    def __init__(self, directory: str) -> None:
        """
        Initialize the HARReader with the directory containing HAR files.

        :param directory: The path to the directory where HAR files are stored.
        """
        self.directory = directory

    def _find_har_file_paths(self) -> Generator[str, None, None]:
        """
        Search for all HAR file paths in the directory.

        :yield: The full path of each HAR file found.
        """
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith(".har"):
                    yield os.path.join(root, file)

    def _read_har_file(self, file_path: str) -> har.HAR:
        """
        Read a HAR file and parse its content.

        :param file_path: The full path to the HAR file.
        :return: The parsed HAR file as a dictionary-like object.
        """
        with open(file_path) as file:
            return cast(har.HAR, json.load(file))

    def get_entries(self) -> List[har.Entry]:
        """
        Retrieve all HTTP entries from the HAR files in the directory.

        :return: A list of HTTP request and response entries from the HAR files.
        """
        entries = []
        for file_path in self._find_har_file_paths():
            har = self._read_har_file(file_path)
            entries.extend(har["log"]["entries"])
        return entries
