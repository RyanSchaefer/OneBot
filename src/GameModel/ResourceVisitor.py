from __future__ import annotations

import abc
from typing import Generic, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from ResourceInterface import Resource
    from StackableResource import StackableResource
    from Item import Item
    from Inventory import Inventory

T = TypeVar('T')


class ResourceVisitor(Generic[T], metaclass=abc.ABCMeta):

    def accept(self, resource: Resource) -> T:
        return resource.visit(self)

    @abc.abstractmethod
    def visit_stackable(self, stackable: StackableResource) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_item(self, item: Item) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_inventory(self, inventory: Inventory) -> T:
        raise NotImplementedError
