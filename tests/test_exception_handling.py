
import pytest
from typing import Generator
from orbis import Effect, OnEffect, UnhandledEffect


class Fetch(Effect[str]):
  tag = "fetch"

  def __init__(self, url: str):
    self.url = url


def test_unhandled_effect_raises():
  """Proves completing mandates all effects are handled."""

  def program() -> Generator[Fetch, str, str]:
    result = yield Fetch("http://example.com")
    return result

  with pytest.raises(UnhandledEffect) as exc_info:
    OnEffect({}).complete(program())

  assert exc_info.value.effect.tag == "fetch"


def test_handler_exception_thrown_into_generator():
  """Proves exceptions are thrown back into the generator."""

  def program() -> Generator[Fetch, str, str]:
    try:
      result = yield Fetch("http://bad.example.com")
    except ValueError:
      result = "fallback"

    return result

  def handle_fetch(effect: Fetch) -> str:
    raise ValueError("network error")

  result = OnEffect({"fetch": handle_fetch}).complete(program())

  assert result == "fallback"


def test_handler_exception_propagates_when_uncaught():
  """Proves handler exceptions reach top-level"""

  def program() -> Generator[Fetch, str, str]:
    result = yield Fetch("http://bad.example.com")
    return result

  def handle_fetch(effect: Fetch) -> str:
    raise ValueError("network error")

  with pytest.raises(ValueError, match="network error"):
    OnEffect({"fetch": handle_fetch}).complete(program())
