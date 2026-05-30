# Exceptions raised by the orbis runtime for unhandled or misused effects.
import types
from typing import Any

from orbis.effects import Effect


class UnhandledEffectError(Exception):
    """Raised when an effect is emitted that has no handler."""

    def __init__(self, effect: Effect[Any], frame: types.FrameType | None = None):
        self.effect = effect
        self.frame = frame

        if frame:
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            funcname = frame.f_code.co_name
            location = f" at {filename}:{lineno} in {funcname}"
        else:
            location = ""

        super().__init__(f"no handler for effect '{effect.tag}'{location}")
