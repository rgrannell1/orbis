"""Handlers are functions that handle effects and events."""

import inspect
from collections.abc import Generator
from typing import Any, Protocol

from orbis.exceptions import UnhandledEffect

type HandlerDict = dict[str, "EffectHandler[Any, Any]"]


class EffectHandler[EffectT, HandlerReturnT](Protocol):
    """A handler is a function that handles an effect."""

    def __call__(self, effect: EffectT) -> HandlerReturnT: ...


def _drive[ReturnT](
    gen: Generator[Any, Any, ReturnT], handlers: HandlerDict
) -> Generator[Any, Any, ReturnT]:
    """Run the generator against the given handlers."""

    send_value = None
    pending_throw = None

    while True:
        try:
            effect = gen.throw(pending_throw) if pending_throw else gen.send(send_value)
        except StopIteration as stop:
            return stop.value

        if effect.tag in handlers:
            try:
                result = handlers[effect.tag](effect)

                if inspect.isgenerator(result):
                    send_value = yield from _drive(result, handlers)
                else:
                    send_value = result

                pending_throw = None
            except Exception as err:
                send_value = None
                pending_throw = err
        else:
            pending_throw = None
            send_value = yield effect


def handle[ReturnT](
    gen: Generator[Any, Any, ReturnT],
    handlers: HandlerDict | None = None,
    **kwargs: EffectHandler[Any, Any],
) -> Generator[Any, Any, ReturnT]:
    """Handle matched effects, bubbling the rest through."""

    merged = {**(handlers or {}), **kwargs}
    return _drive(gen, merged)


def pipe[ReturnT](
    gen: Generator[Any, Any, ReturnT],
    *layers: HandlerDict,
    **kwargs: EffectHandler[Any, Any],
) -> Generator[Any, Any, ReturnT]:
    """Layer handler dicts from left to right; unhandled effects bubble outward."""

    result = gen
    for layer in layers:
        result = handle(result, layer)
    if kwargs:
        result = handle(result, kwargs)
    return result


def complete[ReturnT](
    gen: Generator[Any, Any, ReturnT],
    handlers: HandlerDict | None = None,
    **kwargs: EffectHandler[Any, Any],
) -> ReturnT:
    """Run the generator to completion; raises on any unhandled effect."""

    driven = handle(gen, handlers, **kwargs)
    send_value = None

    while True:
        try:
            effect = driven.send(send_value)
            raise UnhandledEffect(effect)
        except StopIteration as stop:
            return stop.value
