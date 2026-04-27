"""The orbis effect runtime — drive, handle, pipe, tap, and complete."""

import contextvars
import inspect
import types
from collections.abc import Generator
from typing import Any, cast

from orbis.exceptions import UnhandledEffectError
from orbis.orbis_types import EffectHandler, HandlerDict, TapObserver

_effect_source_frame: contextvars.ContextVar[types.FrameType | None] = contextvars.ContextVar("_effect_source_frame", default=None)  # noqa: E501


def _drive[ReturnT](
    gen: Generator[Any, Any, ReturnT], handlers: HandlerDict
) -> Generator[Any, Any, ReturnT]:
    """Run the generator against the given handlers."""

    stack: list[Generator[Any, Any, Any]] = [gen]
    send_value = None
    pending_throw = None

    # We loop until the stack is empty, which means the original generator has returned and all handlers have finished.
    while True:
        current = stack[-1]

        try:
            # If there's a pending exception, throw it into the generator; otherwise, send the last value.
            effect = current.throw(pending_throw) if pending_throw else current.send(send_value)
            pending_throw = None
        except StopIteration as stop:
            # The current generator is done; pop the stack and send its return value to the next one.
            stack.pop()

            if not stack:
                return stop.value

            send_value = stop.value
            pending_throw = None
            continue

        except Exception as err:
            # An exception was raised inside the generator; pop the stack and throw it into the next one.

            stack.pop()
            if not stack:
                raise

            send_value = None
            pending_throw = err
            continue

        if effect.tag in handlers:
            try:
                result = handlers[effect.tag](effect)

                if inspect.isgenerator(result):
                    stack.append(result)
                    send_value = None
                else:
                    send_value = result

                pending_throw = None
            except Exception as err:  # noqa: BLE001
                send_value = None
                pending_throw = err
        else:
            # unhandled effect; bubble up

            _effect_source_frame.set(cast(types.GeneratorType, current).gi_frame)
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


def tap[ReturnT](
    gen: Generator[Any, Any, ReturnT],
    tag: str,
    fn: TapObserver,
) -> Generator[Any, Any, ReturnT]:
    """Observe effects matching tag without consuming them.

    fn(effect) may be a plain function or generator; any effects it yields
    bubble outward. The original effect always continues bubbling unchanged.
    """

    send_value = None
    pending_throw = None

    while True:
        try:
            effect = gen.throw(pending_throw) if pending_throw else gen.send(send_value)
            pending_throw = None
        except StopIteration as stop:
            return stop.value

        if effect.tag == tag:
            result = fn(effect)
            if inspect.isgenerator(result):
                yield from result

        try:
            send_value = yield effect
            pending_throw = None
        except Exception as err:  # noqa: BLE001
            send_value = None
            pending_throw = err


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
            raise UnhandledEffectError(effect, frame=_effect_source_frame.get())
        except StopIteration as stop:
            return stop.value
