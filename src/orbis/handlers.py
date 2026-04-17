
from contextlib import contextmanager
from typing import Any, Generator, Protocol, TypeVar

from orbis.exceptions import UnhandledEffect
from orbis.effects import Effect

ReturnT = TypeVar('ReturnT')


class EffectHandler(Protocol[ReturnT]):
  """
  Effect handlers ... handle effects. Given an effect like `FetchURL`, they define some approach
  to doing that and satisfying the return-type constraint. Effects request _what_ to do; the handlers
  define how it's done.
  """
  def __call__(self, effect: Effect[ReturnT]) -> ReturnT:
    ...


def _drive(gen: Generator, handlers: dict[str, EffectHandler]) -> Generator:
  """Run the generator against the given handlers. """

  send_value = None
  pending_throw = None

  while True:
    try:
      effect = gen.throw(pending_throw) if pending_throw else gen.send(send_value)
    except StopIteration as stop:
      return stop.value

    if effect.tag in handlers:
      try:
        send_value = handlers[effect.tag](effect)
        pending_throw = None
      except Exception as err:
        send_value = None
        pending_throw = err
    else:
      send_value = yield effect
      pending_throw = None


class Handler:
  def __init__(self, handlers: dict[str, EffectHandler]):
    self._handlers = handlers

  def run(self, gen: Generator) -> Generator:
    return _drive(gen, self._handlers)


@contextmanager
def handle(**handlers: EffectHandler):
  yield Handler(handlers)



def orbis(gen: Generator) -> Any:
  "Orbis runs the handled generator to completion"

  send_value = None

  while True:
    try:
      effect = gen.send(send_value)
      raise UnhandledEffect(effect)
    except StopIteration as stop:
      return stop.value
