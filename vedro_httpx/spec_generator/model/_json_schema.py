from typing import Any, Dict, List

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

__all__ = ("to_json_schema", "JsonSchemaVisitor",)


class JsonSchemaVisitor(NodeVisitor[Dict[str, Any]]):
    def __init__(self, *, include_constraints: bool = True) -> None:
        super().__init__()
        self.include_constraints = include_constraints

    def visit_none(self, node: NoneNode, **kwargs: Any) -> Dict[str, Any]:
        return {"type": "null"}

    def visit_bool(self, node: BoolNode, **kwargs: Any) -> Dict[str, Any]:
        return {"type": "boolean"}

    def visit_int(self, node: IntNode, **kwargs: Any) -> Dict[str, Any]:
        schema: Dict[str, Any] = {"type": "integer"}
        if self.include_constraints:
            if node.min_value is not None:
                schema["minimum"] = node.min_value
            if node.max_value is not None:
                schema["maximum"] = node.max_value
        return schema

    def visit_float(self, node: FloatNode, **kwargs: Any) -> Dict[str, Any]:
        schema: Dict[str, Any] = {"type": "number"}
        if self.include_constraints:
            if node.min_value is not None:
                schema["minimum"] = node.min_value
            if node.max_value is not None:
                schema["maximum"] = node.max_value
        return schema

    def visit_str(self, node: StrNode, **kwargs: Any) -> Dict[str, Any]:
        return {"type": "string"}

    def visit_dict(self, node: DictNode, **kwargs: Any) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for key, child in node.keys.items():
            properties[key] = child.accept(self)
            # treat as required if it appeared in all examples (count matches)
            if child.count == node.count:
                required.append(key)
        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    def visit_list(self, node: ListNode, **kwargs: Any) -> Dict[str, Any]:
        items_schema = node.element_type.accept(self) if node.element_type else {}
        schema: Dict[str, Any] = {"type": "array", "items": items_schema}
        if self.include_constraints:
            if node.min_length is not None:
                schema["minItems"] = node.min_length
            if node.max_length is not None:
                schema["maxItems"] = node.max_length
        return schema

    def visit_union(self, node: UnionNode, **kwargs: Any) -> Dict[str, Any]:
        any_of: List[Dict[str, Any]] = [t.accept(self) for t in node.types]
        return {"anyOf": any_of}


def to_json_schema(node: Node, *, include_constraints: bool = True) -> Dict[str, Any]:
    visitor = JsonSchemaVisitor(include_constraints=include_constraints)
    return node.accept(visitor)
