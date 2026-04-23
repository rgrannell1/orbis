"""Types and protocols for the orbis effect runtime."""

from collections.abc import Callable, Generator
from typing import Any, Protocol


class EffectHandler[EffectT, HandlerReturnT](Protocol):
    """A handler is a function that handles an effect."""

    def __call__(self, effect: EffectT) -> HandlerReturnT: ...


type HandlerDict = dict[str, "EffectHandler[Any, Any]"]
type TapObserver = Callable[[Any], Generator[Any, Any, None] | None]
