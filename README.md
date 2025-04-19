# vedro-httpx

[![Codecov](https://img.shields.io/codecov/c/github/vedro-universe/vedro-httpx/main.svg?style=flat-square)](https://codecov.io/gh/vedro-universe/vedro-httpx)
[![PyPI](https://img.shields.io/pypi/v/vedro-httpx.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-httpx/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-httpx?style=flat-square)](https://pypi.python.org/pypi/vedro-httpx/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-httpx.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-httpx/)

> **Vedro ❤ HTTPX** – first‑class [HTTP client](https://www.python-httpx.org/) integration for the [Vedro](https://vedro.io/) framework.

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

## Documentation

All usage examples, advanced configuration, request‑recording and OpenAPI generation guides live in the official docs:

👉 **[https://vedro.io/docs/integrations/httpx-client](https://vedro.io/docs/integrations/httpx-client)**

Check them out to get the most out of *vedro-httpx!*
