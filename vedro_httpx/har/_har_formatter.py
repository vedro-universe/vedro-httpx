from base64 import b64encode
from email.message import Message
from email.parser import Parser
from email.utils import parsedate_to_datetime
from http.cookies import Morsel, SimpleCookie
from typing import Any, List
from urllib.parse import parse_qsl

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
        # httpx does not provide the HTTP version of the request
        formatted_request = self.format_request(request, http_version=response.http_version)
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
        cookies = request.headers.get_list("Cookie")
        formatted: har.Request = {
            "method": request.method,
            "url": str(request.url),
            "httpVersion": http_version,
            "cookies": self._format_cookies(cookies),
            "headers": self.format_headers(request.headers),
            "queryString": self.format_query_params(request.url.params),
            "headersSize": -1,
            "bodySize": -1,
        }
        if request.content:
            formatted["postData"] = self.format_request_post_data(request)
        return formatted

    def format_response(self, response: httpx.Response) -> har.Response:
        cookies = response.headers.get_list("Set-Cookie")
        formatted: har.Response = {
            "status": response.status_code,
            "statusText": response.reason_phrase,
            "httpVersion": response.http_version,
            "cookies": self._format_cookies(cookies),
            "headers": self.format_headers(response.headers),
            "content": self.format_response_content(response),
            "redirectURL": response.headers.get("Location", ""),
            "headersSize": -1,
            "bodySize": -1,
        }
        return formatted

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
            if self._is_text_content(content_type):
                content["text"] = response.content.decode()
            else:
                content["encoding"] = "base64"
                content["text"] = b64encode(response.content).decode()

        return content

    def format_request_post_data(self, request: httpx.Request) -> har.PostData:
        content_type = request.headers.get("Content-Type", "x-unknown")
        post_data: har.PostData = {
            "mimeType": content_type,
            "text": "",
        }
        if content_type.startswith("application/x-www-form-urlencoded"):
            post_data["text"] = request.content.decode()
            post_data["params"] = self._format_url_encoded_params(post_data["text"])
        elif content_type.startswith("multipart/form-data"):
            post_data["text"] = request.content.decode()
            post_data["params"] = self._format_multi_part_params(post_data["text"], content_type)
        elif self._is_text_content(content_type):
            post_data["text"] = request.content.decode()
        else:
            post_data["text"] = "binary"

        return post_data

    def _is_text_content(self, content_type: str) -> bool:
        return content_type.startswith("text/") or content_type.startswith("application/json")

    def _format_url_encoded_params(self, payload: str) -> List[har.PostParam]:
        try:
            parsed = parse_qsl(payload)
        except BaseException:
            return []
        else:
            return [{"name": name, "value": value} for name, value in parsed]

    def _format_multi_part_params(self, payload: str, content_type: str) -> List[har.PostParam]:
        params: List[har.PostParam] = []

        try:
            parser = Parser()
            # Preparing the content in the format required by email.parser
            message: Message = parser.parsestr(f"Content-Type: {content_type}\r\n\r\n{payload}")
            for part in message.get_payload():
                name = part.get_param("name", header="Content-Disposition")
                content_type = part.get_content_type()
                if self._is_text_content(content_type):
                    value = part.get_payload()
                else:
                    value = "(binary)"
                params.append({"name": name, "value": value})
        except BaseException:
            pass

        return params

    def _format_cookies(self, headers: List[str]) -> List[har.Cookie]:
        cookies = []
        for header in headers:
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
                cookie["comment"] = f"Invalid date format: {expires}"
        if morsel["httponly"]:
            cookie["httpOnly"] = True
        if morsel["secure"]:
            cookie["secure"] = True
        return cookie
