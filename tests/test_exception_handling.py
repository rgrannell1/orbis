import pytest
from dataclasses import dataclass
from typing import ClassVar, Generator
from orbis import Effect, UnhandledEffect, complete


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[str] = "fetch"
    url: str


def handle_fetch_raising(effect: EFetch) -> str:
    raise ValueError("network error")


def test_unhandled_effect_raises():
    """Proves completing mandates all effects are handled."""

    def program() -> Generator[EFetch, str, str]:
        result = yield EFetch("http://example.com")
        return result

    with pytest.raises(UnhandledEffect) as exc_info:
        complete(program())

    assert exc_info.value.effect.tag == "fetch"


def test_handler_exception_thrown_into_generator():
    """Proves exceptions are thrown back into the generator."""

    def program() -> Generator[EFetch, str, str]:
        try:
            result = yield EFetch("http://bad.example.com")
        except ValueError:
            result = "fallback"

        return result

    result = complete(program(), fetch=handle_fetch_raising)

    assert result == "fallback"


def test_handler_exception_propagates_when_uncaught():
    """Proves handler exceptions reach top-level"""

    def program() -> Generator[EFetch, str, str]:
        result = yield EFetch("http://bad.example.com")
        return result

    with pytest.raises(ValueError, match="network error"):
        complete(program(), fetch=handle_fetch_raising)
