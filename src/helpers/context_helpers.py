import typing

context_vars = {}


async def set_context_var(key: str, value: typing.Any):
    context_vars[key] = value


async def get_context_var(key: str) -> typing.Any | None:
    if key not in context_vars:
        return None

    return context_vars[key]
