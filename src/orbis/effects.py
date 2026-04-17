"""The core data-types of Orbis. Effects and Events are emitted
and handled."""

from typing import ClassVar


class Effect[ReturnT]:
    """Effects are requests for a handler to do something."""

    tag: ClassVar[str]


class Event(Effect[None]):
    """Events are effects that don't return a value."""

    tag: ClassVar[str]
