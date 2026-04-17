
from typing import Any, Generator, Protocol, TypeVar

from orbis.exceptions import UnhandledEffect
from orbis.effects import Effect

ReturnT = TypeVar('ReturnT')
EffectT_contra = TypeVar('EffectT_contra', contravariant=True, bound='Effect[Any]')
HandlerReturnT_co = TypeVar('HandlerReturnT_co', covariant=True)


class EffectHandler(Protocol[EffectT_contra, HandlerReturnT_co]):
  """
  Effect handlers ... handle effects. Given an effect like `FetchURL`, they define some approach
  to doing that and satisfying the return-type constraint. Effects request _what_ to do; the handlers
  define how it's done.
  """
  def __call__(self, effect: EffectT_contra) -> HandlerReturnT_co:
    ...


def _drive(gen: Generator[Any, Any, ReturnT], handlers: dict[str, EffectHandler[Any, Any]]) -> Generator[Any, Any, ReturnT]:
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


class OnEffect:
  def __init__(self, on_effect: dict[str, EffectHandler[Any, Any]]):
    self._on_effect = on_effect

  def run(self, gen: Generator[Any, Any, ReturnT]) -> Generator[Any, Any, ReturnT]:
    return _drive(gen, self._on_effect)

  def complete(self, gen: Generator[Any, Any, ReturnT]) -> ReturnT:
    driven = self.run(gen)
    send_value = None

    while True:
      try:
        effect = driven.send(send_value)
        raise UnhandledEffect(effect)
      except StopIteration as stop:
        return stop.value


