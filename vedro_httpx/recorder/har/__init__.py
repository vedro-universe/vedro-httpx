# http://www.softwareishard.com/blog/har-12-spec/
import sys
from typing import List, TypedDict

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired

__all__ = ("Creator", "Browser", "PageTimings", "Page", "Cookie", "Header", "QueryParam",
           "PostParam", "PostData", "Content", "Request", "Response", "CacheState", "Cache",
           "Timings", "Entry", "Log")


class Creator(TypedDict):
    # Name of the application/browser used to export the log.
    name: str

    # Version of the application/browser used to export the log.
    version: str

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Browser(Creator):
    pass


class PageTimings(TypedDict):
    #  Content of the page loaded.
    #  Number of milliseconds since page load started (page.startedDateTime).
    #  Use -1 if the timing does not apply to the current request.
    onContentLoad: NotRequired[int]

    # Page is loaded (onLoad event fired).
    # Number of milliseconds since page load started (page.startedDateTime).
    # Use -1 if the timing does not apply to the current request.
    onLoad: NotRequired[int]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Page(TypedDict):
    # Date and time stamp for the beginning of the page load
    # (ISO 8601 - YYYY-MM-DDThh:mm:ss.sTZD, e.g. 2009-07-24T19:20:30.45+01:00).
    startedDateTime: str

    # Unique identifier of a page within the <log>. Entries use it to refer the parent page.
    id: str

    # Page title.
    title: str

    # Detailed timing info about page load.
    pageTimings: PageTimings

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Cookie(TypedDict):
    # The name of the cookie.
    name: str

    # The cookie value.
    value: str

    # The path pertaining to the cookie.
    path: NotRequired[str]

    #  The host of the cookie.
    domain: NotRequired[str]

    # Cookie expiration time.
    # (ISO 8601 - YYYY-MM-DDThh:mm:ss.sTZD, e.g. 2009-07-24T19:20:30.123+02:00).
    expires: NotRequired[str]

    # Set to true if the cookie is HTTP only, false otherwise.
    httpOnly: NotRequired[bool]

    # True if the cookie was transmitted over ssl, false otherwise.
    secure: NotRequired[bool]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Header(TypedDict):
    # The name of the HTTP header.
    name: str

    # The value of the HTTP header.
    value: str

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class QueryParam(TypedDict):
    # The name of the query parameter included in the HTTP request.
    name: str

    # The value of the query parameter.
    value: str

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class PostParam(TypedDict):
    # Name of a posted parameter.
    name: str

    # Value of a posted parameter or content of a posted file.
    value: str

    # Name of a posted file.
    fileName: NotRequired[str]

    # Content type of a posted file.
    contentType: NotRequired[str]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class PostData(TypedDict):
    # Mime type of posted data.
    mimeType: str

    # Plain text posted data
    text: str

    # List of posted parameters (in case of URL encoded parameters).
    params: NotRequired[List[PostParam]]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Content(TypedDict):
    # Length of the returned content in bytes.
    # Should be equal to response.bodySize if there is no compression and bigger when
    # the content has been compressed.
    size: int

    # Number of bytes saved. Leave out this field if the information is not available.
    compression: NotRequired[int]

    # MIME type of the response text (value of the Content-Type response header).
    # The charset attribute of the MIME type is included (if available).
    mimeType: str

    # Response body sent from the server or loaded from the browser cache.
    # This field is populated with textual content only.
    # The text field is either HTTP decoded text or encoded (e.g. "base64") representation
    # of the response body.
    # Leave out this field if the information is not available.
    text: NotRequired[str]

    # Encoding used for response text field e.g "base64".
    # Leave out this field if the text field is HTTP decoded (decompressed & unchunked),
    # than trans-coded from its original character set into UTF-8.
    encoding: NotRequired[str]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Request(TypedDict):
    # Request method (GET, POST, ...).
    method: str

    # Absolute URL of the request (fragments are not included).
    url: str

    # Request HTTP Version.
    httpVersion: str

    # List of cookie objects.
    cookies: List[Cookie]

    # List of header objects.
    headers: List[Header]

    # List of query parameter objects.
    queryString: List[QueryParam]

    # Posted data info.
    postData: NotRequired[PostData]

    # Total number of bytes from the start of the HTTP request message until (and including)
    # the double CRLF before the body.
    # Set to -1 if the info is not available.
    headersSize: int

    # Size of the request body (POST data payload) in bytes.
    # Set to -1 if the info is not available.
    bodySize: int

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Response(TypedDict):
    # Response status.
    status: int

    # Response status description.
    statusText: str

    # Response HTTP Version.
    httpVersion: str

    # List of cookie objects.
    cookies: List[Cookie]

    # List of header objects.
    headers: List[Header]

    # Details about the response body.
    content: Content

    # Redirection target URL from the Location response header.
    redirectURL: str

    # Total number of bytes from the start of the HTTP response message until (and including)
    # the double CRLF before the body.
    # Set to -1 if the info is not available.
    headersSize: int

    # Size of the received response body in bytes.
    # Set to zero in case of responses coming from the cache (304).
    # Set to -1 if the info is not available.
    bodySize: int

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class CacheState(TypedDict):
    # Expiration time of the cache entry.
    expires: NotRequired[str]

    #  The last time the cache entry was opened.
    lastAccess: str

    # ETag
    eTag: str

    # The number of times the cache entry has been opened.
    hitCount: int

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Cache(TypedDict):
    # State of a cache entry before the request.
    # Leave out this field if the information is not available.
    beforeRequest: NotRequired[CacheState]

    # State of a cache entry after the request.
    # Leave out this field if the information is not available.
    afterRequest: NotRequired[CacheState]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Timings(TypedDict):
    # Time spent in a queue waiting for a network connection.
    # Use -1 if the timing does not apply to the current request.
    blocked: NotRequired[int]

    # DNS resolution time. The time required to resolve a host name.
    # Use -1 if the timing does not apply to the current request.
    dns: NotRequired[int]

    # Time required to create TCP connection.
    # Use -1 if the timing does not apply to the current request.
    connect: NotRequired[int]

    # Time required to send HTTP request to the server.
    send: int

    # Waiting for a response from the server.
    wait: int

    # Time required to read entire response from the server (or cache).
    receive: int

    # Time required for SSL/TLS negotiation. If this field is defined then the time is also
    # included in the connect field (to ensure backward compatibility with HAR 1.1).
    # Use -1 if the timing does not apply to the current request.
    ssl: NotRequired[int]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Entry(TypedDict):
    # Reference to the parent page.
    # Leave out this field if the application does not support grouping by pages.
    pageref: NotRequired[str]

    # Date and time stamp of the request start (ISO 8601 - YYYY-MM-DDThh:mm:ss.sTZD).
    startedDateTime: str

    # Total elapsed time of the request in milliseconds.
    # This is the sum of all timings available in the timings object
    # (i.e. not including -1 values).
    time: int

    # Detailed info about the request.
    request: Request

    # Detailed info about the response.
    response: Response

    # Info about cache usage.
    cache: Cache

    # Detailed timing info about request/response round trip.
    timings: Timings

    # IP address of the server that was connected (result of DNS resolution).
    serverIPAddress: NotRequired[str]

    # Unique ID of the parent TCP/IP connection, can be the client or server port number.
    # Note that a port number doesn't have to be unique identifier in cases where the port is
    # shared for more connections. If the port isn't available for the application, any other
    # unique connection ID can be used instead (e.g. connection index).
    # Leave out this field if the application doesn't support this info.
    connection: NotRequired[str]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class Log(TypedDict):
    # Version number of the format. If empty, string "1.1" is assumed by default.
    version: str

    # Name and version info of the log creator application.
    creator: Creator

    # Name and version info of used browser.
    browser: NotRequired[Browser]

    # List of all exported (tracked) pages.
    # Leave out this field if the application does not support grouping by pages.
    pages: NotRequired[List[Page]]

    # List of all exported (tracked) requests.
    entries: List[Entry]

    # A comment provided by the user or the application.
    comment: NotRequired[str]


class HAR(TypedDict):
    # Container for all logging information.
    log: Log
