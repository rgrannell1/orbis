"""Tests for pipe — layered handler composition."""

from dataclasses import dataclass
from collections.abc import Generator
from functools import partial
from typing import ClassVar

from orbis import Effect, Event, complete, handle, pipe


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[LiteralString] = "fetch"
    url: str


@dataclass
class ELog(Event):
    tag: ClassVar[LiteralString] = "log"
    message: str


@dataclass
class EMetric(Event):
    tag: ClassVar[LiteralString] = "metric"
    name: str


ProgramGen = Generator[EFetch | ELog | EMetric, str, str]


def program() -> ProgramGen:

    yield ELog("starting")
    result = yield EFetch("http://example.com")
    yield EMetric("fetch_count")

    return result


def _fetch_url(effect: EFetch) -> str:
    return f"<{effect.url}>"


def _record_message(target: list, effect: ELog) -> None:
    target.append(effect.message)


def _record_name(target: list, effect: EMetric) -> None:
    target.append(effect.name)


def _noop(_) -> None:
    pass


def test_pipe_layers_handlers_left_to_right():
    """Inner layer handles fetch; outer layers handle log and metric separately."""

    logs: list[str] = []
    metrics: list[str] = []

    result = complete(
        pipe(
            program(),
            {"fetch": _fetch_url},
            {"log": partial(_record_message, logs)},
            {"metric": partial(_record_name, metrics)},
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
            {"fetch": _fetch_url},
            {"log": partial(_record_message, logs)},
        ),
        metric=_noop,
    )

    assert result == "<http://example.com>"
    assert logs == ["starting"]


def test_pipe_with_single_layer_matches_handle():
    """pipe with one layer is equivalent to handle."""

    result = complete(
        pipe(program(), {"fetch": _fetch_url}),
        log=_noop,
        metric=_noop,
    )

    assert result == "<http://example.com>"


def test_pipe_kwargs_form():
    """pipe accepts kwargs as a final handler layer."""

    logs: list[str] = []
    metrics: list[str] = []

    result = complete(
        pipe(
            program(),
            {"fetch": _fetch_url},
            log=partial(_record_message, logs),
            metric=partial(_record_name, metrics),
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
                "fetch": _fetch_url,
                "log": partial(_record_message, logs),
                "metric": _noop,
            },
        )
    )

    assert result == "<http://example.com>"
    assert logs == ["starting"]
