"""Tests for pipe — layered handler composition."""

from dataclasses import dataclass
from collections.abc import Generator
from typing import ClassVar

from orbis import Effect, Event, complete, handle, pipe


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[str] = "fetch"
    url: str


@dataclass
class ELog(Event):
    tag: ClassVar[str] = "log"
    message: str


@dataclass
class EMetric(Event):
    tag: ClassVar[str] = "metric"
    name: str


def program() -> Generator[EFetch | ELog | EMetric, str, str]:

    yield ELog("starting")
    result = yield EFetch("http://example.com")
    yield EMetric("fetch_count")

    return result


def test_pipe_layers_handlers_left_to_right():
    """Inner layer handles fetch; outer layers handle log and metric separately."""

    logs: list[str] = []
    metrics: list[str] = []

    result = complete(
        pipe(
            program(),
            {"fetch": lambda effect: f"<{effect.url}>"},
            {"log": lambda effect: logs.append(effect.message)},
            {"metric": lambda effect: metrics.append(effect.name)},
        )
    )

    assert result == "<http://example.com>"
    assert logs == ["starting"]
    assert metrics == ["fetch_count"]


def test_pipe_unhandled_effects_bubble_to_complete():
    """Effects not handled by any pipe layer surface to complete."""

    logs: list[str] = []

    result = complete(
        pipe(
            program(),
            {"fetch": lambda effect: f"<{effect.url}>"},
            {"log": lambda effect: logs.append(effect.message)},
        ),
        metric=lambda effect: None,
    )

    assert result == "<http://example.com>"
    assert logs == ["starting"]


def test_pipe_with_single_layer_matches_handle():
    """pipe with one layer is equivalent to handle."""

    result = complete(
        pipe(program(), {"fetch": lambda effect: f"<{effect.url}>"}),
        log=lambda _: None,
        metric=lambda _: None,
    )

    assert result == "<http://example.com>"


def test_pipe_kwargs_form():
    """pipe accepts kwargs as a final handler layer."""

    logs: list[str] = []
    metrics: list[str] = []

    result = complete(
        pipe(
            program(),
            {"fetch": lambda effect: f"<{effect.url}>"},
            log=lambda effect: logs.append(effect.message),
            metric=lambda effect: metrics.append(effect.name),
        )
    )

    assert result == "<http://example.com>"
    assert logs == ["starting"]
    assert metrics == ["fetch_count"]


def test_handle_positional_dict_form():
    """handle accepts a dict as a positional argument."""

    logs: list[str] = []

    result = complete(
        handle(
            program(),
            {
                "fetch": lambda effect: f"<{effect.url}>",
                "log": lambda effect: logs.append(effect.message),
                "metric": lambda _: None,
            },
        )
    )

    assert result == "<http://example.com>"
    assert logs == ["starting"]
