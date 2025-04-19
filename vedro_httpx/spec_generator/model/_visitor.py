from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from ._nodes import BoolNode, DictNode, FloatNode, IntNode, ListNode, NoneNode, StrNode, UnionNode

__all__ = ("NodeVisitor",)


NodeVisitorRT = TypeVar("NodeVisitorRT")


class NodeVisitor(ABC, Generic[NodeVisitorRT]):
    """
    Defines the visitor interface for traversing and processing `Node` objects.

    This abstract base class provides the structure for visiting each specific
    node type in the tree. Subclasses must implement visit methods corresponding
    to each concrete `Node` subclass.
    """

    @abstractmethod
    def visit_bool(self, node: BoolNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a BoolNode and perform an operation.

        :param node: The boolean node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_none(self, node: NoneNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a NoneNode and perform an operation.

        :param node: The null node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_int(self, node: IntNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit an IntNode and perform an operation.

        :param node: The integer node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_float(self, node: FloatNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a FloatNode and perform an operation.

        :param node: The float node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_str(self, node: StrNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a StrNode and perform an operation.

        :param node: The string node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_dict(self, node: DictNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a DictNode and perform an operation.

        :param node: The dictionary node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_list(self, node: ListNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a ListNode and perform an operation.

        :param node: The list node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()

    @abstractmethod
    def visit_union(self, node: UnionNode, **kwargs: Any) -> NodeVisitorRT:
        """
        Visit a UnionNode and perform an operation.

        :param node: The union node to visit.
        :param kwargs: Additional arguments passed to the visitor.
        :return: The result of the visitor operation.
        """
        raise NotImplementedError()
