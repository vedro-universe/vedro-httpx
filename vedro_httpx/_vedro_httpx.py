from typing import Type

from vedro.core import Dispatcher, Plugin, PluginConfig

__all__ = ("VedroHTTPX", "VedroHTTPXPlugin",)


class VedroHTTPXPlugin(Plugin):
    def __init__(self, config: Type["VedroHTTPX"]) -> None:
        super().__init__(config)

    def subscribe(self, dispatcher: Dispatcher) -> None:
        pass


class VedroHTTPX(PluginConfig):
    plugin = VedroHTTPXPlugin
