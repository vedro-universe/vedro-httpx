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
    def visit_none(self, node: NoneNode, **kwargs: Any) -> str:
        return f"{node.__class__.__name__}(count={node.count})"

    def visit_bool(self, node: BoolNode, **kwargs: Any) -> str:
        return f"{node.__class__.__name__}(count={node.count})"

    def visit_int(self, node: IntNode, **kwargs: Any) -> str:
        args = f"count={node.count}"
        if node.min_value is not None:
            args += f", min_value={node.min_value}"
        if node.max_value is not None:
            args += f", max_value={node.max_value}"
        return f"{node.__class__.__name__}({args})"

    def visit_float(self, node: FloatNode, **kwargs: Any) -> str:
        args = f"count={node.count}"
        if node.min_value is not None:
            args += f", min_value={node.min_value}"
        if node.max_value is not None:
            args += f", max_value={node.max_value}"
        return f"{node.__class__.__name__}({args})"

    def visit_str(self, node: StrNode, **kwargs: Any) -> str:
        return f"{node.__class__.__name__}(count={node.count})"

    def visit_dict(self, node: DictNode, **kwargs: Any) -> str:
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
        indent: int = kwargs.get("indent", 0)

        args = f"count={node.count}"
        if not node.types:
            return f"{node.__class__.__name__}({args})"

        types_str = []
        for t in node.types:
            types_str.append(" " * (indent + 4) + t.accept(self, indent=indent + 4))

        args += f", types=[{linesep}" + f",{linesep}".join(types_str) + f"{linesep}{' ' * indent}]"
        return f"{node.__class__.__name__}({args})"


def format_node(node: Node) -> str:
    if not isinstance(node, Node):
        raise TypeError("Argument must be an instance of Node")

    formatter = NodeFormatter()
    return node.accept(formatter)
