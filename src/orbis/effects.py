"""The core data-types of Orbis. Effects and Events are emitted
and handled."""

from typing import Any, ClassVar, LiteralString


class Effect[ReturnT]:
    """Effects are requests for a handler to do something."""

    tag: ClassVar[LiteralString]

    def __init_subclass__(cls, abstract: bool = False, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not abstract and "tag" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define a 'tag' ClassVar")
        if not abstract and not cls.__dict__.get("tag"):
            raise TypeError(f"{cls.__name__} tag must be a non-empty string")


class Event(Effect[None], abstract=True):
    """Events are effects that don't return a value."""

    tag: ClassVar[LiteralString]
