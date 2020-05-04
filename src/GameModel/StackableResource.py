from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ResourceInterface import Resource, T
    from ResourceVisitor import ResourceVisitor


class StackableResource(Resource, metaclass=ABCMeta):

    def visit(self, visitor: ResourceVisitor[T]) -> T:
        return visitor.visit_stackable(self)

    @abstractmethod
    def get_amount(self):
        raise NotImplementedError
