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
    """
    Converts a Node tree into a JSON Schema representation.

    This visitor traverses each node and generates a corresponding JSON Schema
    definition. It optionally includes constraints such as minimum/maximum values
    for numbers and array length limits.
    """

    def __init__(self, *, include_constraints: bool = True) -> None:
        """
        Initialize the visitor with an option to include value constraints.

        :param include_constraints: Whether to include min/max constraints for numbers
                                    and minItems/maxItems for arrays.
        """
        super().__init__()
        self.include_constraints = include_constraints

    def visit_none(self, node: NoneNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a NoneNode into a JSON Schema representation.

        :param node: The NoneNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for a null type.
        """
        return {"type": "null"}

    def visit_bool(self, node: BoolNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a BoolNode into a JSON Schema representation.

        :param node: The BoolNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for a boolean type.
        """
        return {"type": "boolean"}

    def visit_int(self, node: IntNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert an IntNode into a JSON Schema representation.

        :param node: The IntNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for an integer type,
                 including min/max constraints if enabled.
        """
        schema: Dict[str, Any] = {"type": "integer"}
        if self.include_constraints:
            if node.min_value is not None:
                schema["minimum"] = node.min_value
            if node.max_value is not None:
                schema["maximum"] = node.max_value
        return schema

    def visit_float(self, node: FloatNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a FloatNode into a JSON Schema representation.

        :param node: The FloatNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for a number type,
                 including min/max constraints if enabled.
        """
        schema: Dict[str, Any] = {"type": "number"}
        if self.include_constraints:
            if node.min_value is not None:
                schema["minimum"] = node.min_value
            if node.max_value is not None:
                schema["maximum"] = node.max_value
        return schema

    def visit_str(self, node: StrNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a StrNode into a JSON Schema representation.

        :param node: The StrNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for a string type.
        """
        return {"type": "string"}

    def visit_dict(self, node: DictNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a DictNode into a JSON Schema representation.

        :param node: The DictNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for an object type,
                 including property types and required fields.
        """
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for key, child in node.keys.items():
            properties[key] = child.accept(self)
            if child.count == node.count:
                required.append(key)

        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    def visit_list(self, node: ListNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a ListNode into a JSON Schema representation.

        :param node: The ListNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema for an array type,
                 including item schema and optional length constraints.
        """
        items_schema = node.element_type.accept(self) if node.element_type else {}
        schema: Dict[str, Any] = {"type": "array", "items": items_schema}
        if self.include_constraints:
            if node.min_length is not None:
                schema["minItems"] = node.min_length
            if node.max_length is not None:
                schema["maxItems"] = node.max_length
        return schema

    def visit_union(self, node: UnionNode, **kwargs: Any) -> Dict[str, Any]:
        """
        Convert a UnionNode into a JSON Schema representation using anyOf.

        :param node: The UnionNode to convert.
        :param kwargs: Additional arguments (unused).
        :return: A dictionary representing the JSON Schema with anyOf variants.
        """
        any_of: List[Dict[str, Any]] = [t.accept(self) for t in node.types]
        return {"anyOf": any_of}


def to_json_schema(node: Node, *, include_constraints: bool = True) -> Dict[str, Any]:
    """
    Convert a Node into a JSON Schema representation.

    This function uses the `JsonSchemaVisitor` to traverse the node and generate
    a corresponding JSON Schema dictionary. It supports optional inclusion of
    constraints such as minimum/maximum values or array length bounds.

    :param node: The root Node to convert into JSON Schema.
    :param include_constraints: Whether to include value constraints in the schema.
                                Defaults to True.
    :return: A dictionary representing the JSON Schema for the given node.
    """
    visitor = JsonSchemaVisitor(include_constraints=include_constraints)
    return node.accept(visitor)
