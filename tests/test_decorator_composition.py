from collections.abc import Callable, Generator
from dataclasses import dataclass
from functools import partial, wraps
from typing import ClassVar, LiteralString, cast

from orbis import Effect, Event, complete


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[LiteralString] = "fetch"
    url: str


@dataclass
class ETrace(Event):
    tag: ClassVar[LiteralString] = "trace"
    event: str


type FetchFn[ReturnT] = Callable[..., Generator[EFetch, str, ReturnT]]
type TracedFn[ReturnT] = Callable[..., Generator[EFetch | ETrace, str, ReturnT]]


def traced[ReturnT](fn: FetchFn[ReturnT]) -> TracedFn[ReturnT]:
    """Decorator that emits an ETrace effect before each EFetch."""

    @wraps(fn)
    def wrapper(*args, **kwargs) -> Generator[EFetch | ETrace, str, ReturnT]:
        gen = fn(*args, **kwargs)
        send_value = None

        while True:
            try:
                effect = gen.send(cast(str, send_value))
                if isinstance(effect, EFetch):
                    yield ETrace(f"fetch:{effect.url}")
                send_value = yield effect
            except StopIteration as stop:
                return stop.value

    return wrapper


@traced
def fetch_page() -> Generator[EFetch, str, str]:
    """Fetches two pages and returns their combined length."""

    page_a = yield EFetch("http://example.com/a")
    page_b = yield EFetch("http://example.com/b")

    return f"{page_a},{page_b}"


def handle_fetch(effect: EFetch) -> str:
    return f"<{effect.url}>"


def handle_trace(traces: list[str], effect: ETrace) -> None:
    traces.append(effect.event)


def test_traced_decorator_emits_trace_per_fetch():
    """Proves aspects can be composed onto effectful programs via decorators."""

    traces: list[str] = []

    result = complete(
        fetch_page(), fetch=handle_fetch, trace=partial(handle_trace, traces)
    )

    assert result == "<http://example.com/a>,<http://example.com/b>"
    assert traces == [
        "fetch:http://example.com/a",
        "fetch:http://example.com/b",
    ]
