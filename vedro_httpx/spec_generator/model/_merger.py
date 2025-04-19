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

__all__ = ("create_node", "merge_nodes", "NodeMerger",)


T = TypeVar("T")
R = TypeVar("R")


class NodeMerger(NodeVisitor[Node]):
    """
    Merges two `Node` instances into a single representative node.

    This visitor implementation combines structure and metadata from two
    nodes of the same or compatible types. It is used to aggregate node
    information such as type frequency, bounds (min/max), and structure.

    The merger supports all node types including scalar, list, dict, and union nodes.
    """

    def visit_none(self, node: NoneNode, **kwargs: Any) -> Node:
        """
        Merge two NoneNode instances.

        :param node: The original NoneNode.
        :param kwargs: Additional arguments. Must include 'other', another Node to merge.
        :return: A merged NoneNode or UnionNode if types differ.
        """
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(count=node.count + other.count)

    def visit_bool(self, node: BoolNode, **kwargs: Any) -> Node:
        """
        Merge two BoolNode instances.

        :param node: The original BoolNode.
        :param kwargs: Additional arguments. Must include 'other', another Node to merge.
        :return: A merged BoolNode or UnionNode if types differ.
        """
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(count=node.count + other.count)

    def visit_int(self, node: IntNode, **kwargs: Any) -> Node:
        """
        Merge two IntNode instances, combining count, min, and max values.

        :param node: The original IntNode.
        :param kwargs: Additional arguments. Must include 'other', another Node to merge.
        :return: A merged IntNode or UnionNode if types differ.
        """
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(
            count=node.count + other.count,
            min_value=self._merge_values(node.min_value, other.min_value, min),
            max_value=self._merge_values(node.max_value, other.max_value, max)
        )

    def visit_float(self, node: FloatNode, **kwargs: Any) -> Node:
        """
        Merge two FloatNode instances, combining count, min, and max values.

        :param node: The original FloatNode.
        :param kwargs: Additional arguments. Must include 'other', another Node to merge.
        :return: A merged FloatNode or UnionNode if types differ.
        """
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(
            count=node.count + other.count,
            min_value=self._merge_values(node.min_value, other.min_value, min),
            max_value=self._merge_values(node.max_value, other.max_value, max)
        )

    def visit_str(self, node: StrNode, **kwargs: Any) -> Node:
        """
        Merge two StrNode instances.

        :param node: The original StrNode.
        :param kwargs: Additional arguments. Must include 'other', another Node to merge.
        :return: A merged StrNode or UnionNode if types differ.
        """
        other: Node = kwargs["other"]
        if not isinstance(other, node.__class__):
            return self._merge_nodes(node, other)
        return node.__class__(count=node.count + other.count)

    def visit_dict(self, node: DictNode, **kwargs: Any) -> Node:
        """
        Merge two DictNode instances by merging keys and their corresponding nodes.

        :param node: The original DictNode.
        :param kwargs: Additional arguments. Must include 'other', another DictNode.
        :return: A merged DictNode or UnionNode if types differ.
        """
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
        """
        Merge two ListNode instances by combining element types and list size bounds.

        :param node: The original ListNode.
        :param kwargs: Additional arguments. Must include 'other', another ListNode.
        :return: A merged ListNode or UnionNode if types differ.
        """
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
        """
        Merge a UnionNode with another node or UnionNode.

        :param node: The original UnionNode.
        :param kwargs: Additional arguments. Must include 'other', another Node or UnionNode.
        :return: A merged UnionNode.
        """
        other: Node = kwargs["other"]
        if isinstance(other, UnionNode):
            for t in other.types:
                self._add_or_merge(node, t)
        else:
            self._add_or_merge(node, other)
        node.count += other.count
        return node

    def _add_or_merge(self, node: UnionNode, other: Node) -> None:
        """
        Add a node to a UnionNode, merging if a compatible type exists.

        :param node: The UnionNode to add to.
        :param other: The node to be added or merged into the union.
        """
        for i, existing in enumerate(node.types):
            if type(existing) is type(other):
                node.types[i] = self._merge_nodes(existing, other)
                return
        node.types.append(other)

    def _merge_nodes(self, node1: Node, node2: Node) -> Node:
        """
        Merge two nodes of possibly different types into a compatible node or a union.

        :param node1: The first node to merge.
        :param node2: The second node to merge.
        :return: A merged node or a UnionNode if the types differ.
        """
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
        """
        Merge two optional values using a merging function.

        :param val1: The first value or None.
        :param val2: The second value or None.
        :param merger: A function to combine the two non-None values.
        :return: The merged value, or the non-None value if only one is defined.
        """
        if (val1 is not None) and (val2 is not None):
            return merger(val1, val2)
        return val1 if (val1 is not None) else val2


_merger = NodeMerger()
"""
Default instance of NodeMerger used for merging nodes.

This instance is used internally by the `merge_nodes` function
to perform structural merging of two `Node` instances.
"""


def merge_nodes(node1: Node, node2: Node, *, merger: NodeMerger = _merger) -> Node:
    """
    Merge two `Node` instances into a unified structure.

    This function uses a `NodeMerger` to combine two nodes, preserving type
    and structure where possible. If the nodes are of different types, they
    will be merged into a `UnionNode`.

    :param node1: The first node to merge.
    :param node2: The second node to merge.
    :param merger: Optional custom `NodeMerger` to use for merging.
                   Defaults to a shared internal instance.
    :return: A merged `Node` representing both input nodes.
    :raises TypeError: If either argument is not an instance of `Node`.
    """
    if not isinstance(node1, Node) or not isinstance(node2, Node):
        raise TypeError("Both arguments must be instances of Node")
    return node1.accept(merger, other=node2)


def create_node(value: Any) -> Node:
    """
    Convert a native Python value into a corresponding `Node` instance.

    This function recursively converts standard Python data types into
    the structured `Node` representations used in the specification tree.

    :param value: The value to convert (supports None, bool, int, float,
                  str, list, and dict).
    :return: A `Node` representing the given value.
    :raises TypeError: If the value type is not supported.
    """
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
        keys = {k: create_node(v) for k, v in value.items()}
        return DictNode(keys=keys)
    if isinstance(value, list):
        element_node: Union[Node, None] = None
        for item in value:
            item_node = create_node(item)
            if element_node is None:
                element_node = item_node
            else:
                element_node = merge_nodes(element_node, item_node)
        return ListNode(element_type=element_node, min_length=len(value), max_length=len(value))
    raise TypeError(f"Unsupported type: {type(value)}")
