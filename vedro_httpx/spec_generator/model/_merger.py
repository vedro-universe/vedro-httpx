from typing import Any, Callable, Dict, TypeVar, Union

from ._nodes import (
    BoolNode,
    DictNode,
    FloatNode,
    IntNode,
    ListNode,
    Node,
    NoneNode,
    StrNode,
    UnionNode,
)
from ._visitor import NodeVisitor

__all__ = ("node_from_value", "merge_nodes", "NodeMerger",)


T = TypeVar("T")
R = TypeVar("R")


class NodeMerger(NodeVisitor[Node]):
    def visit_none(self, node: NoneNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(count=node.count + other.count)

    def visit_bool(self, node: BoolNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(count=node.count + other.count)

    def visit_int(self, node: IntNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(
            count=node.count + other.count,
            min_value=self._merge_values(node.min_value, other.min_value, min),
            max_value=self._merge_values(node.max_value, other.max_value, max)
        )

    def visit_float(self, node: FloatNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(
            count=node.count + other.count,
            min_value=self._merge_values(node.min_value, other.min_value, min),
            max_value=self._merge_values(node.max_value, other.max_value, max)
        )

    def visit_str(self, node: StrNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(count=node.count + other.count)

    def visit_dict(self, node: DictNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, DictNode):
            return self._merge_nodes(node, other)

        merged: Dict[str, Node] = {}
        for key in set(node.keys) | set(other.keys):
            a = node.keys.get(key)
            b = other.keys.get(key)
            if a and b:
                merged[key] = self._merge_nodes(a, b)
            else:
                merged[key] = a or b  # type: ignore
        return DictNode(count=node.count + other.count, keys=merged)

    def visit_list(self, node: ListNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if not isinstance(other, ListNode):
            return self._merge_nodes(node, other)
        return ListNode(
            count=node.count + other.count,
            element_type=self._merge_values(node.element_type, other.element_type, merge_nodes),
            min_length=self._merge_values(node.min_length, other.min_length, min),
            max_length=self._merge_values(node.max_length, other.max_length, max),
        )

    def visit_union(self, node: UnionNode, **kwargs: Any) -> Node:
        other: Node = kwargs["other"]
        if isinstance(other, UnionNode):
            for t in other.types:
                self._add_or_merge(node, t)
        else:
            self._add_or_merge(node, other)
        node.count += other.count
        return node

    def _add_or_merge(self, node: UnionNode, other: Node) -> None:
        for i, existing in enumerate(node.types):
            if type(existing) is type(other):
                node.types[i] = self._merge_nodes(existing, other)
                return
        node.types.append(other)

    def _merge_nodes(self, node1: Node, node2: Node) -> Node:
        if type(node1) is type(node2):
            return node1.accept(self, other=node2)
        elif isinstance(node1, UnionNode):
            return node1.accept(self, other=node2)
        elif isinstance(node2, UnionNode):
            return node2.accept(self, other=node1)
        else:
            return UnionNode(count=node1.count + node2.count, types=[node1, node2])

    def _merge_values(self, val1: Union[T, None], val2: Union[T, None],
                      merger: Callable[[T, T], R]) -> Union[T, R, None]:
        if (val1 is not None) and (val2 is not None):
            return merger(val1, val2)
        return val1 if (val1 is not None) else val2


def merge_nodes(node1: Node, node2: Node) -> Node:
    if not isinstance(node1, Node) or not isinstance(node2, Node):
        raise TypeError("Both arguments must be instances of Node")

    merger = NodeMerger()
    return node1.accept(merger, other=node2)


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
        element_node: Union[Node, None] = None
        for item in value:
            item_node = node_from_value(item)
            if element_node is None:
                element_node = item_node
            else:
                element_node = merge_nodes(element_node, item_node)
        return ListNode(element_type=element_node, min_length=len(value), max_length=len(value))
    raise TypeError(f"Unsupported type: {type(value)}")
