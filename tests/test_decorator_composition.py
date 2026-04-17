
from functools import partial, wraps
from typing import Callable, Generator, TypeVar
from orbis import Effect, OnEffect

ReturnT = TypeVar('ReturnT')


class Fetch(Effect[str]):
  tag = "fetch"

  def __init__(self, url: str):
    self.url = url


class Trace(Effect[None]):
  tag = "trace"

  def __init__(self, event: str):
    self.event = event


def traced(
  fn: Callable[..., Generator[Fetch, str, ReturnT]]
) -> Callable[..., Generator[Fetch | Trace, str, ReturnT]]:
  """Decorator that emits a Trace effect before each Fetch."""

  @wraps(fn)
  def wrapper(*args, **kwargs) -> Generator[Fetch | Trace, str, ReturnT]:
    gen = fn(*args, **kwargs)
    send_value = None

    while True:
      try:
        effect = gen.send(send_value)
        if isinstance(effect, Fetch):
          yield Trace(f"fetch:{effect.url}")
        send_value = yield effect
      except StopIteration as stop:
        return stop.value

  return wrapper


@traced
def fetch_page() -> Generator[Fetch, str, str]:
  """Fetches two pages and returns their combined length."""

  a = yield Fetch("http://example.com/a")
  b = yield Fetch("http://example.com/b")

  return f"{a},{b}"


def handle_fetch(effect: Fetch) -> str:
  return f"<{effect.url}>"


def handle_trace(traces: list[str], effect: Trace) -> None:
  traces.append(effect.event)


def test_traced_decorator_emits_trace_per_fetch():
  """Proves aspects can be composed onto effectful programs via decorators."""

  traces: list[str] = []

  result = OnEffect({
    "fetch": handle_fetch,
    "trace": partial(handle_trace, traces),
  }).complete(fetch_page())

  assert result == "<http://example.com/a>,<http://example.com/b>"
  assert traces == [
    "fetch:http://example.com/a",
    "fetch:http://example.com/b",
  ]
