from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypeVar, cast

if TYPE_CHECKING:
    from ._visitor import NodeVisitor

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
    """
    Represents the base class for all node types in the specification tree.

    This abstract class defines the common structure for different types of nodes,
    including a count of occurrences and a visitor interface for processing nodes.
    """
    count: int = 1

    def accept(self, visitor: "NodeVisitor[T]", **kwargs: Any) -> T:
        """
        Accept a visitor that performs an operation on this node.

        :param visitor: The visitor instance implementing the `visit_<type>` method.
        :param kwargs: Additional keyword arguments passed to the visitor.
        :return: The result from the visitor's method.
        """
        kind = self.__class__.__name__[:-4].lower()
        method = getattr(visitor, f"visit_{kind}")
        return cast(T, method(self, **kwargs))


@dataclass
class BoolNode(Node):
    """
    Represents a boolean value node.

    This node type is used to capture and represent boolean values in the spec tree.
    """
    pass


@dataclass
class NoneNode(Node):
    """
    Represents a null value node.

    This node type is used to capture and represent `None` values in the spec tree.
    """
    pass


@dataclass
class IntNode(Node):
    """
    Represents an integer value node.

    This node type captures the occurrence of integer values, along with optional
    minimum and maximum values encountered.

    :param min_value: The smallest integer value encountered, if any.
    :param max_value: The largest integer value encountered, if any.
    """
    min_value: Optional[int] = None
    max_value: Optional[int] = None


@dataclass
class FloatNode(Node):
    """
    Represents a float value node.

    This node type captures the occurrence of floating-point values, along with optional
    minimum and maximum values encountered.

    :param min_value: The smallest float value encountered, if any.
    :param max_value: The largest float value encountered, if any.
    """
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class StrNode(Node):
    """
    Represents a string value node.

    This node type is used to capture and represent string values in the spec tree.
    """
    pass


@dataclass
class DictNode(Node):
    """
    Represents a dictionary (object) node.

    This node holds a mapping of string keys to other node types, capturing
    the structure of JSON-like dictionaries.

    :param keys: A dictionary mapping string keys to corresponding `Node` values.
    """
    keys: Dict[str, Node] = field(default_factory=dict)


@dataclass
class ListNode(Node):
    """
    Represents a list (array) node.

    This node type captures lists with consistent or varying element types,
    and optionally records the minimum and maximum lengths observed.

    :param element_type: The node type of list elements, or None if undetermined.
    :param min_length: The minimum observed length of the list, if known.
    :param max_length: The maximum observed length of the list, if known.
    """
    element_type: Optional[Node] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class UnionNode(Node):
    """
    Represents a union of multiple node types.

    This node is used when values of different types appear in the same field,
    capturing all possible value types as a list of nodes.

    :param types: A list of node types representing each variant in the union.
    """
    types: List[Node] = field(default_factory=list)
