from typing import Any, Dict, List, Set, Tuple

import vedro_httpx.recorder.har as har

__all__ = ("APISpecBuilder",)


class APISpecBuilder:
    def build_spec(self, entries: List[har.Entry]) -> Dict[str, Any]:
        urls = {entry["request"]["url"] for entry in entries}
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
        return (method, path), {
            "total": 0,
            "headers": {},
            "params": {},
            "responses": {},
        }

    def _get_url(self, request: har.Request) -> str:
        return request.get("_parameterized_url", request["url"])

    def _get_base_path(self, urls: Set[str]) -> str:
        parts = [url.split("/") for url in urls]
        common_path = []

        for part in zip(*parts):
            if all(p == part[0] for p in part):
                common_path.append(part[0])
            else:
                break

        return "/".join(common_path)
