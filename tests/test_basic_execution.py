
from typing import Generator
from orbis import Effect, handle, complete

# We'll ping an integer around
MarcoPaloSend = int

# We'll ultimately return the two final counts
MarcoPaloReturn = tuple[int, int]


# Two identical effects
class Marco(Effect[int]):
  tag = "marco"

  def __init__(self, count: int):
    self.count = count


class Polo(Effect[int]):
  tag = "polo"

  def __init__(self, count: int):
    self.count = count


def marco_polo() -> Generator[Marco | Polo, MarcoPaloSend, MarcoPaloReturn]:
  """Out effectful program."""
  marco, polo = 0, 0

  while True:
    marco = yield Marco(marco)
    polo = yield Polo(polo)

    if marco >= 3 and polo >= 3:
      return (marco, polo)


def test_marco_polo_counting():
  """
  Proves nested effects can interplay
  Proves the program runs to completion
  Proves it returns the correct return result.
  """

  def handle_marco(effect: Marco) -> int:
    return effect.count + 1

  def handle_polo(effect: Polo) -> int:
    return effect.count + 1

  with handle(
    marco=handle_marco,
    polo=handle_polo,
  ) as han:
    result = complete(han.run(marco_polo()))

  assert result == (3, 3)
