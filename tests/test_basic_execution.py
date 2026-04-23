"""Tests for basic effect execution — send/receive, void effects, and pure generators."""

from dataclasses import dataclass
from collections.abc import Generator
from typing import ClassVar

from orbis import Effect, Event, complete

# We'll ping an integer around
MarcoPaloSend = int

# We'll ultimately return the two final counts
MarcoPaloReturn = tuple[int, int]


# Two identical effects
@dataclass
class EMarco(Effect[int]):
    tag: ClassVar[LiteralString] = "marco"
    count: int


@dataclass
class EPolo(Effect[int]):
    tag: ClassVar[LiteralString] = "polo"
    count: int


@dataclass
class ENotify(Event):
    tag: ClassVar[LiteralString] = "notify"
    message: str


def handle_marco(effect: EMarco) -> int:
    return effect.count + 1


def handle_polo(effect: EPolo) -> int:
    return effect.count + 1


def marco_polo() -> Generator[EMarco | EPolo, MarcoPaloSend, MarcoPaloReturn]:
    """Out effectful program."""
    marco, polo = 0, 0

    while True:
        marco = yield EMarco(marco)
        polo = yield EPolo(polo)

        if marco >= 3 and polo >= 3:
            return (marco, polo)


def _notify_program(received: list) -> Generator[ENotify, None, str]:
    sent_back = yield ENotify("hello")
    received.append(sent_back)
    return "done"


def _pure_program() -> Generator[Effect, None, int]:
    return 42
    yield  # makes it a generator


def _noop(_) -> None:
    pass


def test_marco_polo_counting():
    """
    Proves nested effects can interplay
    Proves the program runs to completion
    Proves it returns the correct return result.
    """

    result = complete(marco_polo(), marco=handle_marco, polo=handle_polo)

    assert result == (3, 3)


def test_void_effect_sends_none_back():
    """Proves Effect[None] handlers send None back to the generator"""

    received: list[object] = []

    complete(_notify_program(received), notify=_noop)

    assert received == [None]


def test_pure_program_with_no_effects():
    """Proves a generator that yields no effects runs to completion correctly."""

    result = complete(_pure_program())

    assert result == 42
