from typing import Generator, cast

from orbis import Effect, handle, orbis

MarcoPaloSend = int
MarcoPaloReturn = tuple[int, int]


class Marco(Effect[int]):
  tag = "marco"

  def __init__(self, count: int):
    self.count = count


class Polo(Effect[int]):
  tag = "polo"

  def __init__(self, count: int):
    self.count = count


def marco_polo() -> Generator[Marco | Polo, MarcoPaloSend, MarcoPaloReturn]:
  marco, polo = 0, 0
  while True:
    marco = yield Marco(marco)
    polo = yield Polo(polo)
    if marco >= 3 and polo >= 3:
      return (marco, polo)


def test_marco_polo():
  def handle_marco(effect: Effect[int]) -> int:
    assert isinstance(effect, Marco)
    return effect.count + 1

  def handle_polo(effect: Effect[int]) -> int:
    assert isinstance(effect, Polo)
    return effect.count + 1

  with handle(
    marco=handle_marco,
    polo=handle_polo,
  ) as han:
    handled_gen: Generator[None, MarcoPaloSend, MarcoPaloReturn] = cast(
      Generator[None, MarcoPaloSend, MarcoPaloReturn],
      han.run(marco_polo())
    )
    result = orbis(handled_gen)

  assert result == (3, 3)
