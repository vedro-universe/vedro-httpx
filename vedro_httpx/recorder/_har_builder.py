from typing import List, Optional

import vedro_httpx.recorder.har as har

__all__ = ("HARBuilder",)


class HARBuilder:
    def __init__(self, creator_name: str, creator_version: str) -> None:
        self._creator_name = creator_name
        self._creator_version = creator_version

    def build_har(self, log: har.Log) -> har.HAR:
        return {"log": log}

    def build_log(self, entries: List[har.Entry]) -> har.Log:
        log: har.Log = {
            "version": "1.2",
            "creator": self.build_creator(self._creator_name, self._creator_version),
            "entries": entries,
            "pages": [],  # required for some dev tools
        }
        return log

    def build_creator(self, name: str, version: str) -> har.Creator:
        creator: har.Creator = {
            "name": name,
            "version": version,
        }
        return creator

    def build_entry(self,
                    request: har.Request,
                    response: har.Response,
                    started_date_time: str,
                    time: int,
                    server_ip_address: Optional[str] = None) -> har.Entry:
        entry: har.Entry = {
            "startedDateTime": started_date_time,
            "time": time,
            "request": request,
            "response": response,
            "cache": {},
            "timings": {
                "send": 0,
                "wait": 0,
                "receive": 0,
            },
        }
        if server_ip_address is not None:
            entry["serverIPAddress"] = server_ip_address
        return entry

    def build_request(self,
                      method: str,
                      url: str,
                      http_version: str,
                      query_string: List[har.QueryParam],
                      headers: List[har.Header],
                      cookies: List[har.Cookie],
                      post_data: Optional[har.PostData] = None) -> har.Request:
        request: har.Request = {
            "method": method,
            "url": url,
            "httpVersion": http_version,
            "queryString": query_string,
            "headers": headers,
            "cookies": cookies,
            "headersSize": -1,
            "bodySize": -1,
        }
        if post_data is not None:
            request["postData"] = post_data
        return request

    def build_query_param(self, name: str, value: str) -> har.QueryParam:
        query_param: har.QueryParam = {
            "name": name,
            "value": value,
        }
        return query_param

    def build_header(self, name: str, value: str) -> har.Header:
        header: har.Header = {
            "name": name,
            "value": value,
        }
        return header

    def build_cookie(self,
                     name: str,
                     value: str,
                     path: Optional[str] = None,
                     domain: Optional[str] = None,
                     expires: Optional[str] = None,
                     http_only: Optional[bool] = None,
                     secure: Optional[bool] = None,
                     *,
                     comment: Optional[str] = None) -> har.Cookie:
        cookie: har.Cookie = {
            "name": name,
            "value": value,
        }
        if path is not None:
            cookie["path"] = path
        if domain is not None:
            cookie["domain"] = domain
        if expires is not None:
            cookie["expires"] = expires
        if http_only is not None:
            cookie["httpOnly"] = http_only
        if secure is not None:
            cookie["secure"] = secure
        if comment is not None:
            cookie["comment"] = comment
        return cookie

    def build_post_param(self,
                         name: str,
                         value: str,
                         file_name: Optional[str] = None,
                         content_type: Optional[str] = None) -> har.PostParam:
        post_param: har.PostParam = {
            "name": name,
            "value": value,
        }
        if file_name is not None:
            post_param["fileName"] = file_name
        if content_type is not None:
            post_param["contentType"] = content_type
        return post_param

    def build_post_data(self, mime_type: str, text: str,
                        params: Optional[List[har.PostParam]] = None) -> har.PostData:
        post_data: har.PostData = {
            "mimeType": mime_type,
            "text": text,
        }
        if params is not None:
            post_data["params"] = params
        return post_data

    def build_response(self,
                       status: int,
                       status_text: str,
                       http_version: str,
                       cookies: List[har.Cookie],
                       headers: List[har.Header],
                       content: har.Content,
                       redirect_url: str) -> har.Response:
        response: har.Response = {
            "status": status,
            "statusText": status_text,
            "httpVersion": http_version,
            "cookies": cookies,
            "headers": headers,
            "content": content,
            "redirectURL": redirect_url,
            "headersSize": -1,
            "bodySize": -1,
        }
        return response

    def build_response_content(self,
                               mime_type: str,
                               size: int,
                               text: Optional[str] = None,
                               encoding: Optional[str] = None,
                               *,
                               comment: Optional[str] = None) -> har.Content:
        content: har.Content = {
            "size": size,
            "mimeType": mime_type
        }
        if text is not None:
            content["text"] = text
        if encoding is not None:
            content["encoding"] = encoding
        if comment is not None:
            content["comment"] = comment
        return content
