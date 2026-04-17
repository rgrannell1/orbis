
from orbis.effects import Effect


class UnhandledEffect(Exception):
  def __init__(self, effect: Effect):
    self.effect = effect
    super().__init__(f"no handler for effect '{effect.tag}'")
