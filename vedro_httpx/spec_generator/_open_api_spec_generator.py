from typing import Any, Dict, List, Sequence

import yaml

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
    def __init__(self, *, standard_headers: Sequence[str] = STANDARD_HEADERS) -> None:
        self._standard_headers = set(standard_headers)

    def generate_spec(self, api_spec: Dict[str, Any]) -> str:
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "API",
                "version": "1.0.0"
            },
            "servers": [{
                "url": [url for url in api_spec.keys()]
            }],
            "paths": {}
        }

        for base_path, methods in api_spec.items():
            for (method, path), details in methods.items():
                if path not in openapi_spec["paths"]:
                    openapi_spec["paths"][path] = {}
                openapi_spec["paths"][path][method.lower()] = {
                    "summary": f"Endpoint for {method} {path}",
                    "operationId": self._get_operation_id(method, path),
                    "parameters": self._build_params(details) + self._build_headers(details),
                    "responses": self._build_responses(details),
                }

        return yaml.dump(openapi_spec, sort_keys=False, allow_unicode=True)

    def _get_operation_id(self, method: str, path: str) -> str:
        return method.lower() + "_" + path.replace("/", "_").strip("_")

    def _build_params(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
        parameters = []
        for param, info in details["params"].items():
            parameters.append({
                "name": param,
                "in": "query",
                "required": info["requests"] == details["total"],
                "description": "",
                "schema": {
                    "type": "string"
                }
            })
        return parameters

    def _build_headers(self, details: Dict[str, Any]) -> List[Dict[str, Any]]:
        headers = []
        for header, info in details["headers"].items():
            if header.lower() in self._standard_headers:
                continue
            headers.append({
                "name": header,
                "in": "header",
                "required": info["requests"] == details["total"],
                "description": "",
                "schema": {
                    "type": "string"
                }
            })
        return headers

    def _build_responses(self, details: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        responses = {}
        for response_status, response_reason in details["responses"].items():
            responses[str(response_status)] = {
                "description": response_reason
            }
        return responses
