from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ResourceInterface import Resource, T
    from ResourceVisitor import ResourceVisitor


class Item(Resource):

    def visit(self, visitor: ResourceVisitor[T]) -> T:
        raise visitor.visit_item(self)
