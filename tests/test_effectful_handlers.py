from dataclasses import dataclass
from collections.abc import Generator
from typing import ClassVar
from orbis import Effect, Event, complete


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[str] = "fetch"
    url: str


@dataclass
class ECache(Effect[str | None]):
    tag: ClassVar[str] = "cache"
    key: str


@dataclass
class ELog(Event):
    """Fire-and-forget; no response."""

    tag: ClassVar[str] = "log"
    message: str


def program() -> Generator[EFetch, str, str]:
    result = yield EFetch("http://example.com")
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


def test_handler_can_perform_effects():
    """Proves handlers can yield both Events and Effects"""

    logs: list[str] = []
    cache: dict[str, str] = {"http://example.com": "<cached body>"}

    result = complete(program(), fetch=handle_fetch, cache=lambda effect: cache.get(effect.key), log=lambda effect: logs.append(effect.message))

    assert result == "<cached body>"
    assert logs == ["fetching http://example.com", "cache hit: http://example.com"]
