# vedro-httpx

[![Codecov](https://img.shields.io/codecov/c/github/vedro-universe/vedro-httpx/master.svg?style=flat-square)](https://codecov.io/gh/vedro-universe/vedro-httpx)
[![PyPI](https://img.shields.io/pypi/v/vedro-httpx.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-httpx/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-httpx?style=flat-square)](https://pypi.python.org/pypi/vedro-httpx/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-httpx.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-httpx/)

[Vedro](https://vedro.io/) + [HTTPX](https://www.python-httpx.org/)

## Installation

<details open>
<summary>Quick</summary>
<p>

For a quick installation, you can use a plugin manager as follows:

```shell
$ vedro plugin install vedro-httpx
```

</p>
</details>

<details>
<summary>Manual</summary>
<p>

To install manually, follow these steps:

1. Install the package using pip:

```shell
$ pip3 install vedro-httpx
```

2. Next, activate the plugin in your `vedro.cfg.py` configuration file:

```python
# ./vedro.cfg.py
import vedro
import vedro_httpx


class Config(vedro.Config):
    class Plugins(vedro.Config.Plugins):
        class VedroHTTPX(vedro_httpx.VedroHTTPX):
            enabled = True
```

</p>
</details>

## Usage

### AsyncHTTPInterface

```python
from vedro_httpx import Response, AsyncHTTPInterface

class AuthAPI(AsyncHTTPInterface):
    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        super().__init__(base_url)

    async def register(self, creds: dict[str, str]) -> Response:
        return await self._request("POST", "/auth/register", json=creds)
```

### SyncHTTPInterface

```python
from vedro_httpx import Response, AsyncHTTPInterface

class AuthAPI(AsyncHTTPInterface):
    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        super().__init__(base_url)

    async def register(self, creds: dict[str, str]) -> Response:
        return await self._request("POST", "/auth/register", json=creds)
```

## Documentation

Check out the [documentation](https://vedro.io/docs/integrations/httpx-client) for additional information about `vedro-httpx`.
