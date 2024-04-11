from typing import List, Optional

import vedro_httpx.recorder.har as har

__all__ = ("HARBuilder",)


class HARBuilder:
    """
    Builds various components of a HAR (HTTP Archive) file.

    This builder class provides methods to construct different parts of a HAR file
    such as requests, responses, cookies, headers, and the complete HAR object.
    """

    def __init__(self, creator_name: str, creator_version: str) -> None:
        """
        Initialize the HARBuilder with a creator's name and version.

        :param creator_name: The name of the creator.
        :param creator_version: The version of the creator.
        """
        self._creator_name = creator_name
        self._creator_version = creator_version

    def build_har(self, log: har.Log) -> har.HAR:
        """
        Construct a HAR file from a given log.

        :param log: The log to encapsulate in the HAR file.
        :return: A HAR file as a dictionary.
        """
        return {"log": log}

    def build_log(self, entries: List[har.Entry]) -> har.Log:
        """
        Construct a log component for a HAR file.

        :param entries: A list of entry dictionaries.
        :return: A log dictionary.
        """
        log: har.Log = {
            "version": "1.2",
            "creator": self.build_creator(self._creator_name, self._creator_version),
            "entries": entries,
            "pages": [],  # required for some dev tools
        }
        return log

    def build_creator(self, name: str, version: str) -> har.Creator:
        """
        Construct a creator component for a HAR file.

        :param name: The name of the creator.
        :param version: The version of the creator.
        :return: A creator dictionary.
        """
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
        """
        Construct an entry for a HAR log.

        :param request: The request part of the entry.
        :param response: The response part of the entry.
        :param started_date_time: The start time of the request.
        :param time: The total time taken by the request in milliseconds.
        :param server_ip_address: The IP address of the server (optional).
        :return: An entry dictionary.
        """
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
        """
        Construct a request component for a HAR entry.

        :param method: The HTTP method.
        :param url: The URL of the request.
        :param http_version: The HTTP version used.
        :param query_string: A list of query parameters.
        :param headers: A list of headers.
        :param cookies: A list of cookies.
        :param post_data: The data sent in the request body (optional).
        :return: A request dictionary.
        """
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
        """
        Construct a query parameter for a HAR request.

        :param name: The name of the query parameter.
        :param value: The value of the query parameter.
        :return: A query parameter dictionary.
        """
        query_param: har.QueryParam = {
            "name": name,
            "value": value,
        }
        return query_param

    def build_header(self, name: str, value: str) -> har.Header:
        """
        Construct a header for a HAR request.

        :param name: The name of the header.
        :param value: The value of the header.
        :return: A header dictionary.
        """
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
        """
        Construct a cookie for a HAR request.

        :param name: The name of the cookie.
        :param value: The value of the cookie.
        :param path: The path attribute of the cookie (optional).
        :param domain: The domain attribute of the cookie (optional).
        :param expires: The expiration date of the cookie (optional).
        :param http_only: Specifies if the cookie is HTTPOnly (optional).
        :param secure: Specifies if the cookie is secure (optional).
        :param comment: A comment associated with the cookie (optional).
        :return: A cookie dictionary.
        """
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
        """
        Construct a post parameter for a HAR request's post data.

        :param name: The name of the post parameter.
        :param value: The value of the post parameter.
        :param file_name: The file name associated with this post parameter (optional).
        :param content_type: The content type of the post parameter (optional).
        :return: A post parameter dictionary.
        """
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
        """
        Construct post data for a HAR request.

        :param mime_type: The MIME type of the post data.
        :param text: The raw text of the post data.
        :param params: A list of post parameters associated with the post data (optional).
        :return: A post data dictionary.
        """
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
        """
        Construct a response for a HAR entry.

        :param status: The HTTP status code.
        :param status_text: The status text accompanying the HTTP status code.
        :param http_version: The HTTP version used for the response.
        :param cookies: A list of cookies included in the response.
        :param headers: A list of headers included in the response.
        :param content: The content of the response.
        :param redirect_url: The URL to which the response redirects (if any).
        :return: A response dictionary.
        """
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
        """
        Construct content for a HAR response.

        :param mime_type: The MIME type of the content.
        :param size: The size of the content in bytes.
        :param text: The text of the content (optional).
        :param encoding: The encoding of the content text (optional).
        :param comment: A comment about the content (optional).
        :return: A content dictionary.
        """
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
