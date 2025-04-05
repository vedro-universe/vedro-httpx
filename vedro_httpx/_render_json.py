import json
from typing import Any

__all__ = ("get_pretty_json")


def get_pretty_json(code: Any) -> str:
    return json.dumps(code, indent=4, ensure_ascii=False)
