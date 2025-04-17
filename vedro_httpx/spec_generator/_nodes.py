from abc import ABC, abstractmethod
from os import linesep
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

__all__ = ("Node", "BoolNode", "NoneNode", "IntNode", "FloatNode", "StrNode",
           "DictNode", "ListNode", "UnionNode", "merge_nodes", "merge_values", "node_from_value",)


class Node(ABC):
    def __init__(self, count: int = 1, **kwargs: Any) -> None:
        self.count = count

    @abstractmethod
    def merge(self, other: "Node") -> "Node":
        pass

    @abstractmethod
    def to_str(self, indent: int = 0) -> str:
        pass

    def __repr__(self) -> str:
        return self.to_str()


class BoolNode(Node):
    def merge(self, other: Node) -> Node:
        if not isinstance(other, self.__class__):
            return merge_nodes(self, other)
        return self.__class__(count=self.count + other.count)

    def to_str(self, indent: int = 0) -> str:
        return f"{self.__class__.__name__}(count={self.count})"


class NoneNode(Node):
    def merge(self, other: Node) -> Node:
        if not isinstance(other, self.__class__):
            return merge_nodes(self, other)
        return self.__class__(count=self.count + other.count)

    def to_str(self, indent: int = 0) -> str:
        return f"{self.__class__.__name__}(count={self.count})"


class IntNode(Node):
    def __init__(self, count: int = 1, min_value: Optional[int] = None,
                 max_value: Optional[int] = None) -> None:
        super().__init__(count)
        self.min_value = min_value
        self.max_value = max_value

    def merge(self, other: Node) -> Node:
        if not isinstance(other, self.__class__):
            return merge_nodes(self, other)

        return self.__class__(
            count=self.count + other.count,
            min_value=merge_values(self.min_value, other.min_value, min),
            max_value=merge_values(self.max_value, other.max_value, max)
        )

    def to_str(self, indent: int = 0) -> str:
        args = f"count={self.count}"
        if self.min_value is not None:
            args += f", min_value={self.min_value}"
        if self.max_value is not None:
            args += f", max_value={self.max_value}"
        return f"{self.__class__.__name__}({args})"


class FloatNode(Node):
    def __init__(self, count: int = 1, min_value: Optional[float] = None,
                 max_value: Optional[float] = None) -> None:
        super().__init__(count)
        self.min_value = min_value
        self.max_value = max_value

    def merge(self, other: Node) -> Node:
        if not isinstance(other, self.__class__):
            return merge_nodes(self, other)

        return self.__class__(
            count=self.count + other.count,
            min_value=merge_values(self.min_value, other.min_value, min),
            max_value=merge_values(self.max_value, other.max_value, max)
        )

    def to_str(self, indent: int = 0) -> str:
        args = f"count={self.count}"
        if self.min_value is not None:
            args += f", min_value={self.min_value}"
        if self.max_value is not None:
            args += f", max_value={self.max_value}"
        return f"{self.__class__.__name__}({args})"


class StrNode(Node):
    def merge(self, other: Node) -> Node:
        if not isinstance(other, self.__class__):
            return merge_nodes(self, other)
        return self.__class__(count=self.count + other.count)

    def to_str(self, indent: int = 0) -> str:
        return f"{self.__class__.__name__}(count={self.count})"


class DictNode(Node):
    def __init__(self, count: int = 1, keys: Optional[Dict[str, Node]] = None) -> None:
        super().__init__(count)
        self.keys: Dict[str, Node] = keys or {}

    def merge(self, other: Node) -> Node:
        if not isinstance(other, DictNode):
            return merge_nodes(self, other)

        merged: Dict[str, Node] = {}
        for key in set(self.keys) | set(other.keys):
            a = self.keys.get(key)
            b = other.keys.get(key)
            if a and b:
                merged[key] = merge_nodes(a, b)
            else:
                merged[key] = a or b  # type: ignore
        return DictNode(count=self.count + other.count, keys=merged)

    def to_str(self, indent: int = 0) -> str:
        args = f"count={self.count}"
        if not self.keys:
            return f"{self.__class__.__name__}({args})"

        keys_str = []
        for k, v in self.keys.items():
            is_optional = "?" if v.count != self.count else ""
            keys_str.append(" " * (indent + 4) + f"'{k}{is_optional}': {v.to_str(indent + 4)}")

        args += f", keys={{{linesep}" + f",{linesep}".join(keys_str) + f"{linesep}{' ' * indent}}}"
        return f"{self.__class__.__name__}({args})"


class UnionNode(Node):
    def __init__(self, count: int = 1, types: Optional[List[Node]] = None) -> None:
        super().__init__(count)
        self.types: List[Node] = types or []

    def merge(self, other: Node) -> "UnionNode":
        self.count += other.count
        if isinstance(other, UnionNode):
            for t in other.types:
                self._add_or_merge(t)
        else:
            self._add_or_merge(other)
        return self

    def _add_or_merge(self, node: Node) -> None:
        for i, existing in enumerate(self.types):
            if type(existing) is type(node):
                self.types[i] = existing.merge(node)
                return
        self.types.append(node)

    def to_str(self, indent: int = 0) -> str:
        args = f"count={self.count}"
        if not self.types:
            return f"{self.__class__.__name__}({args})"

        types_str = []
        for t in self.types:
            types_str.append(" " * (indent + 4) + t.to_str(indent + 4))

        args += f", types=[{linesep}" + f",{linesep}".join(types_str) + f"{linesep}{' ' * indent}]"
        return f"{self.__class__.__name__}({args})"


class ListNode(Node):
    def __init__(self, count: int = 1, element_type: Optional[Node] = None,
                 min_length: Optional[int] = None,
                 max_length: Optional[int] = None) -> None:
        super().__init__(count)
        self.element_type = element_type
        self.min_length = min_length
        self.max_length = max_length

    def merge(self, other: Node) -> Node:
        if not isinstance(other, ListNode):
            return merge_nodes(self, other)

        return ListNode(
            count=self.count + other.count,
            element_type=merge_values(self.element_type, other.element_type, merge_nodes),
            min_length=merge_values(self.min_length, other.min_length, min),
            max_length=merge_values(self.max_length, other.max_length, max),
        )

    def to_str(self, indent: int = 0) -> str:
        args = f"count={self.count}"
        if self.min_length is not None:
            args += f", min_length={self.min_length}"
        if self.max_length is not None:
            args += f", max_length={self.max_length}"
        if self.element_type is not None:
            element_info = self.element_type.to_str(indent)
            args += f", element_type={element_info}"
        return f"{self.__class__.__name__}({args})"


def merge_nodes(a: Node, b: Node) -> Node:
    if type(a) is type(b):
        return a.merge(b)
    elif isinstance(a, UnionNode):
        return a.merge(b)
    elif isinstance(b, UnionNode):
        return b.merge(a)
    else:
        return UnionNode(count=a.count + b.count, types=[a, b])


T = TypeVar('T')
R = TypeVar('R')


def merge_values(a: Optional[T], b: Optional[T], merger: Callable[[T, T], R]) -> Union[T, R, None]:
    if a is not None and b is not None:
        return merger(a, b)
    elif a is not None:
        return a
    elif b is not None:
        return b
    else:
        return None


def node_from_value(value: Any) -> Node:
    if value is None:
        return NoneNode()
    if isinstance(value, bool):
        return BoolNode()
    if isinstance(value, int):
        return IntNode(min_value=value, max_value=value)
    if isinstance(value, float):
        return FloatNode(min_value=value, max_value=value)
    if isinstance(value, str):
        return StrNode()
    if isinstance(value, dict):
        keys = {k: node_from_value(v) for k, v in value.items()}
        return DictNode(keys=keys)
    if isinstance(value, list):
        element_node: Optional[Node] = None
        for item in value:
            item_node = node_from_value(item)
            if element_node is None:
                element_node = item_node
            else:
                element_node = merge_nodes(element_node, item_node)
        return ListNode(element_type=element_node, min_length=len(value), max_length=len(value))
    raise TypeError(f"Unsupported type: {type(value)}")
