"""Handlers are functions that handle effects and events."""

import inspect
from typing import Any, Generator, Protocol, TypeVar

from orbis.exceptions import UnhandledEffect
from orbis.effects import Effect

ReturnT = TypeVar("ReturnT")
EffectT_contra = TypeVar("EffectT_contra", contravariant=True, bound="Effect[Any]")
HandlerReturnT_co = TypeVar("HandlerReturnT_co", covariant=True)


class EffectHandler(Protocol[EffectT_contra, HandlerReturnT_co]):
    """A handler is a function that handles an effect."""

    def __call__(self, effect: EffectT_contra) -> HandlerReturnT_co: ...


def _drive(
    gen: Generator[Any, Any, ReturnT], handlers: dict[str, EffectHandler[Any, Any]]
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

                # handle the handler generator
                if inspect.isgenerator(result):
                    send_value = yield from _drive(result, handlers)
                else:
                    send_value = result

                pending_throw = None
            except Exception as err:
                send_value = None
                pending_throw = err
        else:
            send_value = yield effect
            pending_throw = None


class OnEffect:
    """A context manager for handling effects."""

    def __init__(self, on_effect: dict[str, EffectHandler[Any, Any]]):
        self._on_effect = on_effect

    def run(self, gen: Generator[Any, Any, ReturnT]) -> Generator[Any, Any, ReturnT]:
        """Run the generator against the given handlers."""

        return _drive(gen, self._on_effect)

    def complete(self, gen: Generator[Any, Any, ReturnT]) -> ReturnT:
        """Complete the generator by returning the final value."""

        driven = self.run(gen)
        send_value = None

        while True:
            try:
                effect = driven.send(send_value)
                raise UnhandledEffect(effect)
            except StopIteration as stop:
                return stop.value
