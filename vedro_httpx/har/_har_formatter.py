from base64 import b64encode
from email.utils import parsedate_to_datetime
from http.cookies import Morsel, SimpleCookie
from typing import Any, List

import httpx

import vedro_httpx
import vedro_httpx.har._types as har

__all__ = ("HARFormatter",)


class HARFormatter:
    def format(self, responses: List[httpx.Response]) -> har.Log:
        return {
            "version": "1.2",
            "creator": {
                "name": "vedro-httpx",
                "version": vedro_httpx.__version__,
            },
            "entries": [self.format_entry(response, response.request) for response in responses],
        }

    def format_entry(self, response: httpx.Response, request: httpx.Request) -> har.Entry:
        formatted_response = self.format_response(response)
        http_version = formatted_response["httpVersion"]  # https://www.python-httpx.org/http2/
        formatted_request = self.format_request(request, http_version=http_version)
        return {
            "startedDateTime": "2021-01-01T00:00:00.000Z",  # update
            "time": 0,  # update
            "request": formatted_request,
            "response": formatted_response,
            "cache": {},
            "timings": {
                "send": 0,
                "wait": 0,
                "receive": 0,
            },
        }

    def format_request(self, request: httpx.Request, *,
                       http_version: str = "HTTP/1.1") -> har.Request:
        return {
            "method": request.method,
            "url": str(request.url),
            "httpVersion": http_version,
            "cookies": [],  # add cookies
            "headers": self.format_headers(request.headers),
            "queryString": self.format_query_params(request.url.params),
            # add postData
            "headersSize": -1,
            "bodySize": -1,
        }

    def format_response(self, response: httpx.Response) -> har.Response:
        http_version = response.extensions.get("http_version", b"HTTP/1.1").decode()
        return {
            "status": response.status_code,
            "statusText": response.reason_phrase,
            "httpVersion": http_version,
            "cookies": self._format_cookies(response),
            "headers": self.format_headers(response.headers),
            "content": self.format_response_content(response),
            "redirectURL": response.headers.get("Location", ""),
            "headersSize": -1,
            "bodySize": -1,
        }

    def format_headers(self, headers: httpx.Headers) -> List[har.Header]:
        return [{"name": key, "value": val} for key, val in headers.multi_items()]

    def format_query_params(self, params: httpx.QueryParams) -> List[har.QueryParam]:
        return [{"name": key, "value": val} for key, val in params.multi_items()]

    def format_response_content(self, response: httpx.Response) -> har.Content:
        content_type = response.headers.get("Content-Type", "x-unknown")
        content: har.Content = {
            "size": len(response.content),
            "mimeType": content_type,
        }

        if len(response.content) > 0:
            if content_type.startswith("text/") or content_type.startswith("application/json"):
                content["text"] = response.content.decode()
            else:
                content["encoding"] = "base64"
                content["text"] = b64encode(response.content).decode()

        return content

    def _format_cookies(self, response: httpx.Response) -> List[har.Cookie]:
        cookies = []
        for header in response.headers.get_list("Set-Cookie"):
            cookie: SimpleCookie[Any] = SimpleCookie()
            cookie.load(header)
            for name, morsel in cookie.items():
                cookies.append(self._format_cookie(name, morsel))
        return cookies

    def _format_cookie(self, name: str, morsel: "Morsel[Any]") -> har.Cookie:
        cookie: har.Cookie = {"name": name, "value": morsel.value}
        if path := morsel["path"]:
            cookie["path"] = path
        if domain := morsel["domain"]:
            cookie["domain"] = domain
        if expires := morsel["expires"]:
            try:
                cookie["expires"] = parsedate_to_datetime(expires).isoformat()
            except BaseException:
                pass
        if morsel["httponly"]:
            cookie["httpOnly"] = True
        if morsel["secure"]:
            cookie["secure"] = True
        return cookie
