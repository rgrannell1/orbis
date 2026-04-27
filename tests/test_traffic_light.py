"""Tests for a traffic light state machine — effectful handlers driving state transitions."""

from collections.abc import Generator
from dataclasses import dataclass
from functools import partial
from typing import ClassVar, LiteralString

from orbis import Effect, Event, complete


@dataclass
class ETransition(Effect[str]):
    """Request a transition from the current phase; returns the next phase."""

    tag: ClassVar[LiteralString] = "transition"
    phase: str


@dataclass
class EBroadcast(Event):
    """Notify external systems of a phase change."""

    tag: ClassVar[LiteralString] = "broadcast"
    message: str


@dataclass
class ELog(Event):
    tag: ClassVar[LiteralString] = "log"
    message: str


TRANSITIONS: dict[str, str] = {"red": "green", "green": "yellow", "yellow": "red"}


def traffic_light(cycles: int) -> Generator[ETransition, str, None]:
    phase = "red"

    for _ in range(cycles * 3):
        phase = yield ETransition(phase)


def handle_transition(effect: ETransition) -> Generator[ELog | EBroadcast, None, str]:
    """On transition, do something"""

    next_phase = TRANSITIONS[effect.phase]

    yield ELog(f"{effect.phase} → {next_phase}")
    yield EBroadcast(f"phase:{next_phase}")

    return next_phase


def _record_message(target: list, effect: ELog) -> None:
    target.append(effect.message)


def _record_broadcast(target: list, effect: EBroadcast) -> None:
    target.append(effect.message)


def _noop(_) -> None:
    pass


def test_traffic_light_transitions_and_broadcasts():
    """Proves effectful handlers can drive state transitions while emitting their own effects."""

    logs: list[str] = []
    broadcasts: list[str] = []

    complete(
        traffic_light(cycles=1),
        transition=handle_transition,
        log=partial(_record_message, logs),
        broadcast=partial(_record_broadcast, broadcasts),
    )

    assert logs == ["red → green", "green → yellow", "yellow → red"]
    assert broadcasts == ["phase:green", "phase:yellow", "phase:red"]


def test_traffic_light_multiple_cycles():
    """Proves effectful state machines loop as expected"""

    logs: list[str] = []

    complete(
        traffic_light(cycles=2),
        transition=handle_transition,
        log=partial(_record_message, logs),
        broadcast=_noop,
    )

    assert logs == [
        "red → green",
        "green → yellow",
        "yellow → red",
        "red → green",
        "green → yellow",
        "yellow → red",
    ]
