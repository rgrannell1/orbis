
from typing import ClassVar, Generic, TypeVar

ReturnT = TypeVar('ReturnT')


class Effect(Generic[ReturnT]):
  tag: ClassVar[str]


class Event(Effect[None]):
  pass
