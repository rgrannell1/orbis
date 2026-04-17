"""Handlers are functions that handle effects and events."""

import inspect
from collections.abc import Generator
from typing import Any, Protocol

from orbis.exceptions import UnhandledEffect
from orbis.effects import Effect

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
            send_value = yield effect
            pending_throw = None


class OnEffect:
    """Binds a set of handlers to a generator."""

    def __init__(self, on_effect: HandlerDict):
        self._on_effect = on_effect

    def run[ReturnT](self, gen: Generator[Any, Any, ReturnT]) -> Generator[Any, Any, ReturnT]:
        """Run the generator against the given handlers."""

        return _drive(gen, self._on_effect)

    def complete[ReturnT](self, gen: Generator[Any, Any, ReturnT]) -> ReturnT:
        """Complete the generator by returning the final value."""

        driven = self.run(gen)
        send_value = None

        while True:
            try:
                effect = driven.send(send_value)
                raise UnhandledEffect(effect)
            except StopIteration as stop:
                return stop.value


def complete[ReturnT](gen: Generator[Any, Any, ReturnT], **handlers: EffectHandler[Any, Any]) -> ReturnT:
    return OnEffect(handlers).complete(gen)


def run[ReturnT](gen: Generator[Any, Any, ReturnT], **handlers: EffectHandler[Any, Any]) -> Generator[Any, Any, ReturnT]:
    return OnEffect(handlers).run(gen)
