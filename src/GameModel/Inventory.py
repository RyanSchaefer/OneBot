from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from ResourceInterface import Resource


class Inventory(Resource, metaclass=ABCMeta):

    @abstractmethod
    def get_items(self) -> List[Resource]:
        raise NotImplementedError

    @abstractmethod
    def place(self, resource: Resource):
        raise NotImplementedError

    @abstractmethod
    def remove(self, resource: Resource, slot: int = 0, amount: int = 1):
        raise NotImplementedError

    @abstractmethod
    def get_dimensions(self) -> Tuple[int, int]:
        raise NotImplementedError
