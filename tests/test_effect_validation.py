from typing import ClassVar, LiteralString

import pytest

from orbis import Effect, Event


def test_effect_without_tag_raises_at_class_definition():
    """Proves defining an Effect subclass without a tag fails immediately."""

    with pytest.raises(TypeError, match="must define a 'tag' ClassVar"):

        class EBroken(Effect[str]):
            pass


def test_event_without_tag_raises_at_class_definition():
    """Proves defining an Event subclass without a tag fails immediately."""

    with pytest.raises(TypeError, match="must define a 'tag' ClassVar"):

        class EBrokenEvent(Event):
            pass


def test_effect_with_tag_is_valid():
    """Proves a well-formed Effect subclass is accepted."""

    class EOk(Effect[str]):
        tag: ClassVar[LiteralString] = "ok"


def test_abstract_subclass_does_not_require_tag():
    """Proves intermediate abstract Effect subclasses can omit tag."""

    class EBase(Effect[str], abstract=True):
        pass

    class EConcrete(EBase):
        tag: ClassVar[LiteralString] = "concrete"
