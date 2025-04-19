from os import linesep
from typing import Any

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

__all__ = ("format_node", "NodeFormatter",)


class NodeFormatter(NodeVisitor[str]):
    """
    Converts Node instances into human-readable string representations.

    This visitor is primarily used for debugging or displaying node structures
    in a structured format. It supports pretty-printing of nested objects
    and union types with indentation.
    """

    def visit_none(self, node: NoneNode, **kwargs: Any) -> str:
        """
        Format a NoneNode as a string.

        :param node: The NoneNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A string representation of the NoneNode.
        """
        return f"{node.__class__.__name__}(count={node.count})"

    def visit_bool(self, node: BoolNode, **kwargs: Any) -> str:
        """
        Format a BoolNode as a string.

        :param node: The BoolNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A string representation of the BoolNode.
        """
        return f"{node.__class__.__name__}(count={node.count})"

    def visit_int(self, node: IntNode, **kwargs: Any) -> str:
        """
        Format an IntNode as a string.

        :param node: The IntNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A string representation of the IntNode including min/max if set.
        """
        args = f"count={node.count}"
        if node.min_value is not None:
            args += f", min_value={node.min_value}"
        if node.max_value is not None:
            args += f", max_value={node.max_value}"
        return f"{node.__class__.__name__}({args})"

    def visit_float(self, node: FloatNode, **kwargs: Any) -> str:
        """
        Format a FloatNode as a string.

        :param node: The FloatNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A string representation of the FloatNode including min/max if set.
        """
        args = f"count={node.count}"
        if node.min_value is not None:
            args += f", min_value={node.min_value}"
        if node.max_value is not None:
            args += f", max_value={node.max_value}"
        return f"{node.__class__.__name__}({args})"

    def visit_str(self, node: StrNode, **kwargs: Any) -> str:
        """
        Format a StrNode as a string.

        :param node: The StrNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A string representation of the StrNode.
        """
        return f"{node.__class__.__name__}(count={node.count})"

    def visit_dict(self, node: DictNode, **kwargs: Any) -> str:
        """
        Format a DictNode as a string, recursively formatting its keys and values.

        :param node: The DictNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A multi-line string representing the DictNode.
        """
        indent: int = kwargs.get("indent", 0)

        args = f"count={node.count}"
        if not node.keys:
            return f"{node.__class__.__name__}({args})"

        keys_str = []
        for k, v in node.keys.items():
            is_optional = "?" if v.count != node.count else ""
            keys_str.append(
                " " * (indent + 4) + f"'{k}{is_optional}': {v.accept(self, indent=indent + 4)}"
            )

        args += f", keys={{{linesep}" + f",{linesep}".join(keys_str) + f"{linesep}{' ' * indent}}}"
        return f"{node.__class__.__name__}({args})"

    def visit_list(self, node: ListNode, **kwargs: Any) -> str:
        """
        Format a ListNode as a string, including element type and length constraints.

        :param node: The ListNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A string representation of the ListNode.
        """
        indent: int = kwargs.get("indent", 0)

        args = f"count={node.count}"
        if node.min_length is not None:
            args += f", min_length={node.min_length}"
        if node.max_length is not None:
            args += f", max_length={node.max_length}"
        if node.element_type is not None:
            element_info = node.element_type.accept(self, indent=indent)
            args += f", element_type={element_info}"
        return f"{node.__class__.__name__}({args})"

    def visit_union(self, node: UnionNode, **kwargs: Any) -> str:
        """
        Format a UnionNode as a string, recursively formatting each union member.

        :param node: The UnionNode instance to format.
        :param kwargs: Optional formatting options (e.g., indent level).
        :return: A multi-line string representation of the UnionNode.
        """
        indent: int = kwargs.get("indent", 0)

        args = f"count={node.count}"
        if not node.types:
            return f"{node.__class__.__name__}({args})"

        types_str = []
        for t in node.types:
            types_str.append(" " * (indent + 4) + t.accept(self, indent=indent + 4))

        args += f", types=[{linesep}" + f",{linesep}".join(types_str) + f"{linesep}{' ' * indent}]"
        return f"{node.__class__.__name__}({args})"


_formatter = NodeFormatter()
"""
Default instance of NodeFormatter used for formatting nodes.

This shared formatter is used by the `format_node` function to create
human-readable string representations of node structures.
"""


def format_node(node: Node, *, formatter: NodeFormatter = _formatter) -> str:
    """
    Generate a human-readable string representation of a Node.

    This function uses the `NodeFormatter` visitor to recursively format the given
    node into a structured and optionally indented string. It is primarily used for
    debugging and visual inspection of the node hierarchy.

    :param node: The Node instance to be formatted.
    :param formatter: Optional custom formatter instance to use. Defaults to a
                      shared internal `NodeFormatter`.
    :return: A formatted string representing the structure and contents of the node.
    :raises TypeError: If the argument is not an instance of Node.
    """
    if not isinstance(node, Node):
        raise TypeError("Argument must be an instance of Node")
    return node.accept(formatter)
