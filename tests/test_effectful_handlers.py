"""Tests for handlers that are themselves generators, yielding their own effects."""

from collections.abc import Generator
from dataclasses import dataclass
from functools import partial
from typing import ClassVar, LiteralString

from orbis import Effect, Event, complete


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[LiteralString] = "fetch"
    url: str


@dataclass
class ECache(Effect[str | None]):
    tag: ClassVar[LiteralString] = "cache"
    key: str


@dataclass
class ELog(Event):
    """Fire-and-forget; no response."""

    tag: ClassVar[LiteralString] = "log"
    message: str


def program() -> Generator[EFetch, str, str]:
    result = yield EFetch("http://example.com")
    return result


def _program_catching_value_error() -> Generator[EFetch, str, str]:
    try:
        result = yield EFetch("http://example.com")
    except ValueError:
        result = "caught"
    return result


def handle_fetch(effect: EFetch) -> Generator[ELog | ECache, str | None, str]:
    """Handler that uses both Event (ELog) and Effect (ECache)."""

    yield ELog(f"fetching {effect.url}")
    cached = yield ECache(effect.url)

    if cached is not None:
        yield ELog(f"cache hit: {effect.url}")
        return cached

    yield ELog(f"cache miss: {effect.url}")
    return f"<body of {effect.url}>"


def handle_fetch_raising(effect: EFetch) -> Generator[ELog, str, str]:
    yield ELog("before raise")
    raise ValueError("sub-handler error")


def _record_message(target: list, effect: ELog) -> None:
    target.append(effect.message)


def _cache_lookup(cache: dict, effect: ECache) -> str | None:
    return cache.get(effect.key)


def test_effectful_handler_exception_thrown_into_program():
    """Proves exceptions raised inside a generator handler are thrown back into the program."""

    logs: list[str] = []

    result = complete(
        _program_catching_value_error(),
        fetch=handle_fetch_raising,
        log=partial(_record_message, logs),
    )

    assert result == "caught"
    assert logs == ["before raise"]


def test_handler_can_perform_effects():
    """Proves handlers can yield both Events and Effects"""

    logs: list[str] = []
    cache: dict[str, str] = {"http://example.com": "<cached body>"}

    result = complete(
        program(),
        fetch=handle_fetch,
        cache=partial(_cache_lookup, cache),
        log=partial(_record_message, logs),
    )

    assert result == "<cached body>"
    assert logs == ["fetching http://example.com", "cache hit: http://example.com"]
