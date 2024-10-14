from typing import Any, Dict, List, Set, Tuple
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

    def build_spec(self, entries: List[har.Entry]) -> Dict[str, Any]:
        """
        Build an API specification from the given HAR entries.

        :param entries: A list of HAR entries containing HTTP request and response data.
        :return: A dictionary representing the API specification.
        """
        urls = {self._get_url(entry["request"]) for entry in entries}
        base_path = self._get_base_path(urls)

        spec: Dict[str, Any] = {
            base_path: {}
        }

        for entry in entries:
            method, url = entry["request"]["method"], self._get_url(entry["request"])
            path = url[len(base_path):]

            route, details = self._create_route(method, path)
            if route not in spec[base_path]:
                spec[base_path][route] = details

            spec[base_path][route]["total"] += 1

            params = entry["request"]["queryString"]
            for param in params:
                name, value = param["name"], param["value"]
                if name not in spec[base_path][route]["params"]:
                    spec[base_path][route]["params"][name] = {"requests": 0, "example": value}
                spec[base_path][route]["params"][name]["requests"] += 1

            headers = entry["request"]["headers"]
            for header in headers:
                name, value = header["name"].lower(), header["value"]
                if name not in spec[base_path][route]["headers"]:
                    spec[base_path][route]["headers"][name] = {"requests": 0, "example": value}
                spec[base_path][route]["headers"][name]["requests"] += 1

            response_status = entry["response"]["status"]
            response_reason = entry["response"]["statusText"]
            spec[base_path][route]["responses"][response_status] = response_reason

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

    def _get_base_path(self, urls: Set[str]) -> str:
        """
        Determine the common base path from a set of URLs.

        :param urls: A set of URLs from the HAR entries.
        :return: The common base path shared by the URLs.
        """
        parts = [url.split("/") for url in urls]
        common_path = []

        for part in zip(*parts):
            if all(p == part[0] for p in part):
                common_path.append(part[0])
            else:
                break

        return "/".join(common_path)
