import json
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import vedro_httpx.recorder.har as har

from ._visitors import merge_nodes, node_from_value

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
        spec: Dict[str, Any] = {}
        groups = self._group_entries_by_origin(entries, base_url)
        for origin, group_entries in groups.items():
            origin_spec: Dict[Tuple[str, str], Dict[str, Any]] = {}
            for entry in group_entries:
                self._process_entry(origin_spec, entry, origin)
            spec[origin] = origin_spec
        return spec

    def _process_entry(self, origin_spec: Dict[Tuple[str, str], Dict[str, Any]],
                       entry: har.Entry, origin: str) -> None:
        method = entry["request"]["method"]
        url = self._get_url(entry["request"])
        path = url[len(origin):] or "/"

        key = (method, path)
        if key not in origin_spec:
            origin_spec[key] = self._init_route_details()

        details = origin_spec[key]
        details["total"] += 1

        self._aggregate_params(details, entry["request"]["queryString"])
        self._aggregate_headers(details, entry["request"]["headers"])
        self._aggregate_request_body(details, entry["request"])
        self._aggregate_response_body(details, entry["response"])

    def _init_route_details(self) -> Dict[str, Any]:
        return {
            "total": 0,
            "headers": {},
            "params": {},
            "body": {"requests": 0, "payload": None},
            "responses": {},
        }

    def _aggregate_params(self, details: Dict[str, Any], params: List[har.QueryParam]) -> None:
        for param in params:
            name, value = param["name"], param["value"]
            stats = details["params"].setdefault(name, {"requests": 0, "example": value})
            stats["requests"] += 1

    def _aggregate_headers(self, details: Dict[str, Any], headers: List[har.Header]) -> None:
        for header in headers:
            name, value = header["name"].lower(), header["value"]
            stats = details["headers"].setdefault(name, {"requests": 0, "example": value})
            stats["requests"] += 1

    def _aggregate_request_body(self, details: Dict[str, Any], request: har.Request) -> None:
        if "postData" not in request:
            return
        body = self._extract_json_body(request["postData"])
        if body is None:
            return

        details["body"]["requests"] += 1

        if details["body"]["payload"] is not None:
            details["body"]["payload"] = merge_nodes(
                details["body"]["payload"],
                node_from_value(body)
            )
        else:
            details["body"]["payload"] = node_from_value(body)

    def _aggregate_response_body(self, details: Dict[str, Any], response: har.Response) -> None:
        status = response["status"]
        resp = details["responses"].setdefault(status, {
            "requests": 0,
            "reason": response["statusText"],
            "body": None,
        })
        resp["requests"] += 1

        if "content" not in response:
            return
        body = self._extract_json_body(response["content"])
        if body is None:
            return

        if resp["body"] is not None:
            resp["body"] = merge_nodes(resp["body"], node_from_value(body))
        else:
            resp["body"] = node_from_value(body)

    def _extract_json_body(self, data: Union[har.PostData, har.Content]) -> Any:
        text = data.get("text", "")
        mime = data.get("mimeType", "").lower()
        if mime.startswith("application/json") and text:
            return json.loads(text)
        return None

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
            groups.setdefault(group_key, []).append(entry)
        return groups
