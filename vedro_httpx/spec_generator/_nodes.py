from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypeVar, cast

if TYPE_CHECKING:
    from ._visitors import NodeVisitor


__all__ = ("Node", "BoolNode", "NoneNode", "IntNode", "FloatNode", "StrNode",
           "DictNode", "ListNode", "UnionNode",)

T = TypeVar("T")


class Node(ABC):
    def __init__(self, count: int = 1, **kwargs: Any) -> None:
        self.count = count

    def accept(self, visitor: NodeVisitor[T], **kwargs: Any) -> T:
        kind = self.__class__.__name__[:-4].lower()
        method = getattr(visitor, f"visit_{kind}")
        return cast(T, method(self, **kwargs))


class BoolNode(Node):
    pass


class NoneNode(Node):
    pass


class IntNode(Node):
    def __init__(self, count: int = 1, min_value: Optional[int] = None,
                 max_value: Optional[int] = None) -> None:
        super().__init__(count)
        self.min_value = min_value
        self.max_value = max_value


class FloatNode(Node):
    def __init__(self, count: int = 1, min_value: Optional[float] = None,
                 max_value: Optional[float] = None) -> None:
        super().__init__(count)
        self.min_value = min_value
        self.max_value = max_value


class StrNode(Node):
    pass


class DictNode(Node):
    def __init__(self, count: int = 1, keys: Optional[Dict[str, Node]] = None) -> None:
        super().__init__(count)
        self.keys: Dict[str, Node] = keys or {}


class UnionNode(Node):
    def __init__(self, count: int = 1, types: Optional[List[Node]] = None) -> None:
        super().__init__(count)
        self.types: List[Node] = types or []


class ListNode(Node):
    def __init__(self, count: int = 1, element_type: Optional[Node] = None,
                 min_length: Optional[int] = None,
                 max_length: Optional[int] = None) -> None:
        super().__init__(count)
        self.element_type = element_type
        self.min_length = min_length
        self.max_length = max_length
