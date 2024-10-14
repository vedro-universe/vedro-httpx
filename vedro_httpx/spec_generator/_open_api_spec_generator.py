from typing import Any, Dict, List, Sequence

import yaml

from ._utils import humanize_identifier

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

    This class provides methods to generate an OpenAPI specification based on
    API request methods, parameters, headers, and response codes, excluding
    standard headers like 'accept' or 'content-type' by default.
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
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "API",
                "version": "1.0.0"
            },
            "servers": [{"url": url} for url in api_spec.keys()],
            "paths": {}
        }

        for base_path, methods in api_spec.items():
            for (method, path), details in methods.items():
                if path not in openapi_spec["paths"]:
                    openapi_spec["paths"][path] = {}  # type: ignore
                openapi_spec["paths"][path][method.lower()] = {  # type: ignore
                    "summary": f"Endpoint for {method} {path}",
                    "operationId": self._get_operation_id(method, path),
                    "parameters": self._build_params(details) + self._build_headers(details),
                    "responses": self._build_responses(details),
                }

        return yaml.dump(openapi_spec, sort_keys=False, allow_unicode=True)

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

    def _build_responses(self, details: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Build the responses section of the OpenAPI spec.

        :param details: A dictionary containing details of API responses.
        :return: A dictionary mapping HTTP status codes to response descriptions.
        """
        responses = {}
        for response_status, response_reason in details["responses"].items():
            responses[str(response_status)] = {
                "description": response_reason
            }
        return responses
