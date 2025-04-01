from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import vedro_httpx.recorder.har as har

__all__ = ("APISpecBuilder",)


class APISpecBuilder:
    """
    Builds a structured API specification from a list of HAR entries.

    This class processes HTTP request and response data from HAR entries,
    organizing them into an API specification format suitable for further
    documentation or testing.
    """

    def build_spec(self, entries: List[har.Entry],
                   base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Build an API specification from the given HAR entries.

        If a base_url is provided, only entries whose full URL starts with the base_url
        are processed, and the specification is grouped under the base_url. Otherwise,
        entries are grouped by their origin (scheme://netloc).

        :param entries: A list of HAR entries containing HTTP request and response data.
        :param base_url: Optional base URL to filter and group entries.
        :return: A dictionary representing the API specification.
        """
        spec: Dict[str, Any] = {}

        groups = self._group_entries_by_origin(entries, base_url=base_url)
        for base_origin, group_entries in groups.items():
            spec[base_origin] = {}
            for entry in group_entries:
                method, url = entry["request"]["method"], self._get_url(entry["request"])
                path = url[len(base_origin):]
                if path == "":
                    path = "/"

                route, details = self._create_route(method, path)
                if route not in spec[base_origin]:
                    spec[base_origin][route] = details

                spec[base_origin][route]["total"] += 1

                params = entry["request"]["queryString"]
                for param in params:
                    name, value = param["name"], param["value"]
                    if name not in spec[base_origin][route]["params"]:
                        spec[base_origin][route]["params"][name] = {
                            "requests": 0,
                            "example": value
                        }
                    spec[base_origin][route]["params"][name]["requests"] += 1

                headers = entry["request"]["headers"]
                for header in headers:
                    name, value = header["name"].lower(), header["value"]
                    if name not in spec[base_origin][route]["headers"]:
                        spec[base_origin][route]["headers"][name] = {
                            "requests": 0,
                            "example": value
                        }
                    spec[base_origin][route]["headers"][name]["requests"] += 1

                response_status = entry["response"]["status"]
                response_reason = entry["response"]["statusText"]
                spec[base_origin][route]["responses"][response_status] = response_reason

        return spec

    def _create_route(self, method: str, path: str) -> Tuple[Tuple[str, str], Dict[str, Any]]:
        """
        Create a route dictionary for an API method and path.

        :param method: The HTTP method (e.g., GET, POST).
        :param path: The API endpoint path.
        :return: A tuple containing the method-path tuple and the route details dictionary.
        """
        return (method, path), {
            "total": 0,
            "headers": {},
            "params": {},
            "responses": {},
        }

    def _get_url(self, request: har.Request) -> str:
        """
        Extract the full URL from a HAR request object.

        :param request: A dictionary containing the HAR request data.
        :return: The full URL as a string.
        """
        parsed_url = urlparse(request.get("_parameterized_url", request["url"]))
        return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    def _group_entries_by_origin(self, entries: List[har.Entry],
                                 base_url: Optional[str] = None) -> Dict[str, List[har.Entry]]:
        """
        Group HAR entries by their origin or by a specified base URL.

        When a base URL is provided, only entries whose full URL starts with the base URL
        are included, and they are grouped under the base URL key. Otherwise, entries are grouped
        by their origin (scheme://netloc).

        :param entries: A list of HAR entries.
        :param base_url: Optional base URL to filter and group entries.
        :return: A dictionary mapping each origin or the provided base URL to a list of
                 corresponding entries.
        """
        if base_url:
            base_url = base_url.rstrip("/")

        groups: Dict[str, List[har.Entry]] = {}

        for entry in entries:
            url = self._get_url(entry["request"])
            parsed = urlparse(url)
            group_key = base_url if base_url else f"{parsed.scheme}://{parsed.netloc}"

            if not url.startswith(group_key):
                continue

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(entry)

        return groups
