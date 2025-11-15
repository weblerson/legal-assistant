import typing

T = typing.TypeVar("T")


class ContextKey(typing.Generic[T]):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name


context_vars: dict[str, typing.Any] = {}


async def set_context_var(key: ContextKey[T], value: T):
    context_vars[key.name] = value


async def get_context_var(key: ContextKey[T]) -> T | None:
    if key.name not in context_vars:
        return None

    return typing.cast(T, context_vars[key.name])
