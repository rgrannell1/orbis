"""Tests for tap — observe effects without consuming them."""

from dataclasses import dataclass
from collections.abc import Generator
from typing import ClassVar

from orbis import Effect, Event, complete, tap


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[str] = "fetch"
    url: str


@dataclass
class ELog(Event):
    tag: ClassVar[str] = "log"
    message: str


def program() -> Generator[EFetch, str, str]:
    result = yield EFetch("http://example.com")
    return result


def test_tap_does_not_consume_effect():
    """Proves tapped effect is still handled by the outer handler."""

    result = complete(
        tap(program(), "fetch", lambda _: None),
        fetch=lambda effect: f"<{effect.url}>",
    )

    assert result == "<http://example.com>"


def test_tap_fn_is_called_for_matching_tag():
    """Proves fn is called exactly once per matching effect."""

    seen: list[str] = []

    complete(
        tap(program(), "fetch", lambda e: seen.append(e.url)),
        fetch=lambda effect: f"<{effect.url}>",
    )

    assert seen == ["http://example.com"]


def test_tap_fn_not_called_for_non_matching_tag():
    """Proves fn is not called for effects with a different tag."""

    seen: list[str] = []

    complete(
        tap(program(), "log", lambda e: seen.append(e.message)),
        fetch=lambda effect: f"<{effect.url}>",
    )

    assert seen == []


def test_tap_generator_fn_can_yield_effects():
    """Proves fn may yield its own effects that bubble outward."""

    logs: list[str] = []

    def observe(effect: EFetch) -> Generator[ELog, None, None]:
        yield ELog(f"tapping {effect.url}")

    result = complete(
        tap(program(), "fetch", observe),
        fetch=lambda effect: f"<{effect.url}>",
        log=lambda effect: logs.append(effect.message),
    )

    assert result == "<http://example.com>"
    assert logs == ["tapping http://example.com"]


def test_tap_original_effect_value_reaches_program():
    """Proves the program receives the handler's return value, not None."""

    received: list[str] = []

    def capture() -> Generator[EFetch, str, None]:
        val = yield EFetch("http://example.com")
        received.append(val)

    complete(
        tap(capture(), "fetch", lambda _: None),
        fetch=lambda effect: "the-body",
    )

    assert received == ["the-body"]
