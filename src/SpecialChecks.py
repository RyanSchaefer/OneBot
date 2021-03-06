from functools import wraps
from typing import Callable, TypeVar, Generic, Any, Tuple

import discord

T = TypeVar("T")


class EventCheck(Generic[T]):
    """
    A check to be added for an event like on_message
    :type T An event type
    """
    def __init__(self, predicate: Callable[[discord.Client, T, Tuple[Any, ...]], bool]):
        self.predicate = predicate

    def __call__(self, func):
        @wraps(func)
        async def wrapper(bot_self: discord.Client, event: T, *args):
            if self.predicate(bot_self, event, *args):
                await func(bot_self, event, *args)
            else:
                return
        return wrapper


class EventCheckAny(Generic[T]):
    """
    A check to be added for an event like on_message, checks if at least one of the
    predicates is true
    :type T An event type
    """

    def __init__(self, *predicates: Tuple[Callable[[discord.Client, T, Tuple[Any, ...]], bool], ...]):
        self.predicates = predicates

    def __call__(self, func):
        @wraps(func)
        async def wrapper(bot_self: discord.Client, event: T, *args):
            if any(map(lambda x: x(bot_self, event, *args), self.predicates)):
                await func(bot_self, event, *args)
            else:
                return
        return wrapper