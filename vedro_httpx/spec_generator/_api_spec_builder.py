import json
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import vedro_httpx.recorder.har as har

from .model._merger import merge_nodes, node_from_value

__all__ = ("APISpecBuilder",)


class APISpecBuilder:
    """
    Builds a structured API specification from a list of HAR entries.

    This class processes HTTP request and response data from HAR entries,
    organizing them into an API specification format. It aggregates headers,
    parameters, request bodies, and responses to form a comprehensive structure
    suitable for documentation or testing.
    """

    def build_spec(self, entries: List[har.Entry],
                   base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Build an API specification from a list of HAR entries.

        :param entries: A list of HAR entries containing request and response data.
        :param base_url: Optional base URL to group entries by. If provided, only entries
                         starting with this base URL are included.
        :return: A dictionary mapping base URLs or origins to endpoint specifications.
        """
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
        """
        Process a single HAR entry and update the specification data.

        :param origin_spec: A dictionary storing the endpoint details per (method, path).
        :param entry: The HAR entry containing request and response information.
        :param origin: The origin or base URL for this entry.
        """
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
        """
        Initialize the structure for an API route's specification details.

        :return: A dictionary with initialized keys for headers, params, body, and responses.
        """
        return {
            "total": 0,
            "headers": {},
            "params": {},
            "body": {
                "requests": 0,
                "content": {},
            },
            "responses": {},
        }

    def _aggregate_params(self, details: Dict[str, Any], params: List[har.QueryParam]) -> None:
        """
        Aggregate query parameter data from the request into the API spec.

        :param details: The current details dictionary for the route.
        :param params: A list of query parameters from the HAR entry.
        """
        for param in params:
            name, value = param["name"], param["value"]
            stats = details["params"].setdefault(name, {"requests": 0, "example": value})
            stats["requests"] += 1

    def _aggregate_headers(self, details: Dict[str, Any], headers: List[har.Header]) -> None:
        """
        Aggregate header data from the request into the API spec.

        :param details: The current details dictionary for the route.
        :param headers: A list of headers from the HAR entry.
        """
        for header in headers:
            name, value = header["name"].lower(), header["value"]
            stats = details["headers"].setdefault(name, {"requests": 0, "example": value})
            stats["requests"] += 1

    def _aggregate_request_body(self, details: Dict[str, Any], request: har.Request) -> None:
        """
        Aggregate request body data into the API spec.

        :param details: The current details dictionary for the route.
        :param request: The request object from the HAR entry.
        """
        if "postData" not in request:
            return

        post = request["postData"]
        mime = post["mimeType"].lower()

        raw = None
        if mime.startswith("application/json"):
            raw = self._extract_json_body(post)
        elif mime.startswith("application/x-www-form-urlencoded"):
            raw = self._extract_form_body(post)
        if raw is None:
            return

        details["body"]["requests"] += 1
        entry = details["body"]["content"].setdefault(mime, {"requests": 0, "payload": None})
        entry["requests"] += 1

        if entry["payload"] is None:
            entry["payload"] = node_from_value(raw)
        else:
            entry["payload"] = merge_nodes(entry["payload"], node_from_value(raw))

    def _aggregate_response_body(self, details: Dict[str, Any], response: har.Response) -> None:
        """
        Aggregate response body data into the API spec.

        :param details: The current details dictionary for the route.
        :param response: The response object from the HAR entry.
        """
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
        """
        Extract and parse JSON body content from HAR data.

        :param data: A HAR postData or content object.
        :return: The parsed JSON object, or None if parsing fails.
        """
        text = data.get("text", "")
        try:
            return json.loads(text)
        except:  # noqa: E722
            return None

    def _extract_form_body(self, data: har.PostData) -> Any:
        """
        Extract and parse form-encoded body content.

        :param data: A HAR postData object containing URL-encoded form data.
        :return: A dictionary representing the parsed form data, or None on failure.
        """
        text = data.get("text", "")
        try:
            raw = parse_qs(text, keep_blank_values=True)
            return {k: v if len(v) > 1 else v[0] for k, v in raw.items()}
        except:  # noqa: E722
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
