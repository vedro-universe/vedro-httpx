from typing import Any, Dict, List, Sequence

import yaml

from ._utils import humanize_identifier
from .model import to_json_schema

__all__ = ("OpenAPISpecGenerator",)


STANDARD_HEADERS = (
    "host",
    "accept",
    "accept-encoding",
    "connection",
    "user-agent",
    "content-length",
    "content-type"
)


class OpenAPISpecGenerator:
    """
    Generates an OpenAPI specification from API request and response data.

    This class transforms structured API specifications (usually generated
    from HAR entries) into a YAML-formatted OpenAPI 3.0 specification.
    It excludes common standard headers by default, and includes support
    for parameters, request bodies, and responses.
    """

    def __init__(self, *, standard_headers: Sequence[str] = STANDARD_HEADERS) -> None:
        """
        Initialize the OpenAPISpecGenerator with standard headers to be excluded.

        :param standard_headers: A sequence of headers to be excluded from the spec,
                                 defaults to standard headers like 'accept' and 'content-type'.
        """
        self._standard_headers = set(standard_headers)

    def generate_spec(self, api_spec: Dict[str, Any]) -> str:
        """
        Generate the OpenAPI specification for the given API.

        :param api_spec: A dictionary containing the API's base paths, methods, and details.
        :return: The generated OpenAPI specification in YAML format.
        """
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "API", "version": "1.0.0"},
            "servers": self._build_servers(api_spec),
            "paths": self._build_paths(api_spec),
        }
        return yaml.dump(spec, sort_keys=False, allow_unicode=True)

    def _build_servers(self, api_spec: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build the 'servers' section of the OpenAPI document.

        :param api_spec: A dictionary of the API specification grouped by base URL.
        :return: A list of server objects, each containing a 'url' key.
        """
        return [{"url": url} for url in api_spec.keys()]

    def _build_paths(self, api_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the 'paths' section of the OpenAPI document.

        :param api_spec: A dictionary of the API specification grouped by base URL.
        :return: A dictionary representing all paths and methods in the API.
        """
        paths: Dict[str, Any] = {}
        for base_path, methods in api_spec.items():
            for (method, route), details in methods.items():
                path_item = paths.setdefault(route, {})
                operation = self._create_operation(method, route, details)
                path_item[method.lower()] = operation
        return paths

    def _create_operation(self, method: str, path: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an operation object for a specific HTTP method and route.

        :param method: The HTTP method (e.g., 'GET', 'POST').
        :param path: The route path of the endpoint.
        :param details: A dictionary of request/response details for this route.
        :return: A dictionary representing the OpenAPI operation object.
        """
        operation: Dict[str, Any] = {
            "summary": f"Endpoint for {method} {path}",
            "operationId": self._get_operation_id(method, path),
            "parameters": self._build_params(details) + self._build_headers(details),
        }
        request_body = self._build_request_body(details)
        if request_body:
            operation["requestBody"] = request_body
        operation["responses"] = self._build_responses(details)
        return operation

    def _build_params(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build the query parameters section of the OpenAPI spec.

        :param details: A dictionary containing details of API parameters.
        :return: A list of dictionaries representing each query parameter.
        """
        parameters = []
        for param, info in details["params"].items():
            parameters.append({
                "name": param,
                "in": "query",
                "required": info["requests"] == details["total"],
                "description": f"{humanize_identifier(param)} param",
                "schema": {
                    "type": "string"
                }
            })
        return parameters

    def _build_headers(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build the headers section of the OpenAPI spec.

        :param details: A dictionary containing details of request headers.
        :return: A list of dictionaries representing each request header.
        """
        headers = []
        for header, info in details["headers"].items():
            if header.lower() in self._standard_headers:
                continue
            headers.append({
                "name": header,
                "in": "header",
                "required": info["requests"] == details["total"],
                "description": f"{humanize_identifier(header)} header",
                "schema": {
                    "type": "string"
                }
            })
        return headers

    def _build_request_body(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the requestBody section for an operation.

        :param details: A dictionary containing body payloads and content types.
        :return: A dictionary representing the OpenAPI requestBody object.
        """
        body = details["body"]
        if body["requests"] == 0:
            return {}

        content: Dict[str, Any] = {}
        for mime, info in body["content"].items():
            schema = to_json_schema(info["payload"])
            content[mime] = {"schema": schema}

        return {
            "description": "Request body",
            "required": body["requests"] == details["total"],
            "content": content
        }

    def _build_responses(self, details: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Build the responses section of the OpenAPI spec.

        :param details: A dictionary containing details of API responses.
        :return: A dictionary mapping HTTP status codes to response descriptions.
        """
        responses = {}
        for status, info in details["responses"].items():
            response = {"description": info["reason"]}
            if info["body"] is not None:
                response["content"] = {
                    "application/json": {"schema": to_json_schema(info["body"])}
                }
            responses[str(status)] = response
        return responses

    def _get_operation_id(self, method: str, path: str) -> str:
        """
        Generate a unique operation ID for an API method and path.

        :param method: The HTTP method (e.g., GET, POST).
        :param path: The API endpoint path.
        :return: A unique operation ID string.
        """
        replacements = {"/": "_", "{": "", "}": ""}
        for old, new in replacements.items():
            path = path.replace(old, new)
        return method.lower() + "_" + path.strip("_")
