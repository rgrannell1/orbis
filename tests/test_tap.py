"""Tests for tap — observe effects without consuming them."""

from collections.abc import Generator
from dataclasses import dataclass
from functools import partial
from typing import ClassVar, LiteralString

from orbis import Effect, Event, complete, tap


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[LiteralString] = "fetch"
    url: str


@dataclass
class ELog(Event):
    tag: ClassVar[LiteralString] = "log"
    message: str


def program() -> Generator[EFetch, str, str]:
    result = yield EFetch("http://example.com")
    return result


def _capture_program(received: list) -> Generator[EFetch, str, None]:
    val = yield EFetch("http://example.com")
    received.append(val)


def _fetch_url(effect: EFetch) -> str:
    return f"<{effect.url}>"


def _return_body(_) -> str:
    return "the-body"


def _noop(_) -> None:
    pass


def _record_url(target: list, effect: EFetch) -> None:
    target.append(effect.url)


def _record_message(target: list, effect: ELog) -> None:
    target.append(effect.message)


def test_tap_does_not_consume_effect():
    """Proves tapped effect is still handled by the outer handler."""

    result = complete(
        tap(program(), "fetch", _noop),
        fetch=_fetch_url,
    )

    assert result == "<http://example.com>"


def test_tap_fn_is_called_for_matching_tag():
    """Proves fn is called exactly once per matching effect."""

    seen: list[str] = []

    complete(
        tap(program(), "fetch", partial(_record_url, seen)),
        fetch=_fetch_url,
    )

    assert seen == ["http://example.com"]


def test_tap_fn_not_called_for_non_matching_tag():
    """Proves fn is not called for effects with a different tag."""

    seen: list[str] = []

    complete(
        tap(program(), "log", partial(_record_message, seen)),
        fetch=_fetch_url,
    )

    assert seen == []


def test_tap_generator_fn_can_yield_effects():
    """Proves fn may yield its own effects that bubble outward."""

    logs: list[str] = []

    def observe(effect: EFetch) -> Generator[ELog, None, None]:
        yield ELog(f"tapping {effect.url}")

    result = complete(
        tap(program(), "fetch", observe),
        fetch=_fetch_url,
        log=partial(_record_message, logs),
    )

    assert result == "<http://example.com>"
    assert logs == ["tapping http://example.com"]


def test_tap_original_effect_value_reaches_program():
    """Proves the program receives the handler's return value, not None."""

    received: list[str] = []

    complete(
        tap(partial(_capture_program, received)(), "fetch", _noop),
        fetch=_return_body,
    )

    assert received == ["the-body"]
