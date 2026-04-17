
from typing import Generator
from orbis import Effect, Event, OnEffect

# We'll ping an integer around
MarcoPaloSend = int

# We'll ultimately return the two final counts
MarcoPaloReturn = tuple[int, int]


# Two identical effects
class EMarco(Effect[int]):
  tag = "marco"

  def __init__(self, count: int):
    self.count = count


class EPolo(Effect[int]):
  tag = "polo"

  def __init__(self, count: int):
    self.count = count


def marco_polo() -> Generator[EMarco | EPolo, MarcoPaloSend, MarcoPaloReturn]:
  """Out effectful program."""
  marco, polo = 0, 0

  while True:
    marco = yield EMarco(marco)
    polo = yield EPolo(polo)

    if marco >= 3 and polo >= 3:
      return (marco, polo)


def test_marco_polo_counting():
  """
  Proves nested effects can interplay
  Proves the program runs to completion
  Proves it returns the correct return result.
  """

  def handle_marco(effect: EMarco) -> int:
    return effect.count + 1

  def handle_polo(effect: EPolo) -> int:
    return effect.count + 1

  result = OnEffect({"marco": handle_marco, "polo": handle_polo}).complete(marco_polo())

  assert result == (3, 3)


class ENotify(Event):
  tag = "notify"

  def __init__(self, message: str):
    self.message = message


def test_void_effect_sends_none_back():
  """Proves Effect[None] handlers send None back to the generator"""

  received: list[object] = []

  def program() -> Generator[ENotify, None, str]:

    sent_back = yield ENotify("hello")
    received.append(sent_back)
    return "done"

  OnEffect({"notify": lambda effect: None}).complete(program())

  assert received == [None]


def test_pure_program_with_no_effects():
  """Proves a generator that yields no effects runs to completion correctly."""

  def program() -> Generator[Effect, None, int]:
    return 42
    yield  # makes it a generator

  result = OnEffect({}).complete(program())

  assert result == 42
