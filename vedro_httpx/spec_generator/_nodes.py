from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypeVar, cast

if TYPE_CHECKING:
    from ._visitors import NodeVisitor

T = TypeVar("T")

__all__ = (
    "Node",
    "BoolNode",
    "NoneNode",
    "IntNode",
    "FloatNode",
    "StrNode",
    "DictNode",
    "ListNode",
    "UnionNode",
)


@dataclass
class Node(ABC):
    count: int = 1

    def accept(self, visitor: "NodeVisitor[T]", **kwargs: Any) -> T:
        kind = self.__class__.__name__[:-4].lower()
        method = getattr(visitor, f"visit_{kind}")
        return cast(T, method(self, **kwargs))


@dataclass
class BoolNode(Node):
    pass


@dataclass
class NoneNode(Node):
    pass


@dataclass
class IntNode(Node):
    min_value: Optional[int] = None
    max_value: Optional[int] = None


@dataclass
class FloatNode(Node):
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class StrNode(Node):
    pass


@dataclass
class DictNode(Node):
    keys: Dict[str, Node] = field(default_factory=dict)


@dataclass
class ListNode(Node):
    element_type: Optional[Node] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class UnionNode(Node):
    types: List[Node] = field(default_factory=list)
