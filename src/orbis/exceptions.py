from typing import Any
from orbis.effects import Effect


class UnhandledEffect(Exception):
    """Raised when an effect is emitted that has no handler."""

    def __init__(self, effect: Effect[Any]):
        self.effect = effect
        super().__init__(f"no handler for effect '{effect.tag}'")
