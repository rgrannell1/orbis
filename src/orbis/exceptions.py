import types
from typing import Any
from orbis.effects import Effect


class UnhandledEffect(Exception):
    """Raised when an effect is emitted that has no handler."""

    def __init__(self, effect: Effect[Any], frame: types.FrameType | None = None):
        self.effect = effect
        self.frame = frame

        if frame:
            location = f" at {frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}"
        else:
            location = ""

        super().__init__(f"no handler for effect '{effect.tag}'{location}")
