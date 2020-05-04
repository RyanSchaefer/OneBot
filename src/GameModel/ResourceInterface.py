from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ResourceVisitor import ResourceVisitor, T


class Resource(metaclass=ABCMeta):

    @abstractmethod
    def get_name(self):
        raise NotImplementedError

    @abstractmethod
    def get_item_id(self):
        raise NotImplementedError

    @abstractmethod
    def visit(self, visitor: ResourceVisitor[T]) -> T:
        raise NotImplementedError
