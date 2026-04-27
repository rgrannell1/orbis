"""Repository pattern example using algebraic effects — a peach inventory store."""

from dataclasses import dataclass
from collections.abc import Generator
from functools import partial
from typing import Any, ClassVar

from orbis import Effect, Event, HandlerDict, complete


PeachData = dict[str, Any]
PeachStore = dict[str, PeachData]


@dataclass
class EPeachGet(Effect[PeachData | None]):
    tag: ClassVar[LiteralString] = "peach_get"
    peach_id: str


@dataclass
class EPeachSave(Event):
    tag: ClassVar[LiteralString] = "peach_save"
    peach_id: str
    data: PeachData


@dataclass
class EPeachDelete(Event):
    tag: ClassVar[LiteralString] = "peach_delete"
    peach_id: str


@dataclass
class EPeachList(Effect[list[str]]):
    tag: ClassVar[LiteralString] = "peach_list"


# --- Programs ---


def save_and_retrieve(
    peach_id: str, data: PeachData
) -> Generator[EPeachSave | EPeachGet, PeachData | None, PeachData | None]:
    yield EPeachSave(peach_id, data)
    return (yield EPeachGet(peach_id))


def fetch_only(
    peach_id: str,
) -> Generator[EPeachGet, PeachData | None, PeachData | None]:
    return (yield EPeachGet(peach_id))


def delete_then_fetch(
    peach_id: str,
) -> Generator[EPeachSave | EPeachDelete | EPeachGet, PeachData | None, PeachData | None]:
    yield EPeachSave(peach_id, {"variety": "Elberta"})
    yield EPeachDelete(peach_id)
    return (yield EPeachGet(peach_id))


def save_many_then_list(
    entries: list[tuple[str, PeachData]],
) -> Generator[EPeachSave | EPeachList, list[str], list[str]]:
    for peach_id, data in entries:
        yield EPeachSave(peach_id, data)
    return (yield EPeachList())


def overwrite_peach(
    peach_id: str,
) -> Generator[EPeachSave | EPeachGet, PeachData | None, PeachData | None]:
    yield EPeachSave(peach_id, {"sweetness": 7})
    yield EPeachSave(peach_id, {"sweetness": 10})
    return (yield EPeachGet(peach_id))


# --- Handlers ---


def handle_get(store: PeachStore, effect: EPeachGet) -> PeachData | None:
    return store.get(effect.peach_id)


def handle_save(store: PeachStore, effect: EPeachSave) -> None:
    store[effect.peach_id] = effect.data


def handle_delete(store: PeachStore, effect: EPeachDelete) -> None:
    store.pop(effect.peach_id, None)


def handle_list(store: PeachStore, effect: EPeachList) -> list[str]:
    return list(store.keys())


def make_handlers(store: PeachStore) -> HandlerDict:
    return {
        "peach_get": partial(handle_get, store),
        "peach_save": partial(handle_save, store),
        "peach_delete": partial(handle_delete, store),
        "peach_list": partial(handle_list, store),
    }


# --- Tests ---


def test_save_and_retrieve_peach():
    """Proves a repository can store and retrieve a peach via effects."""

    result = complete(
        save_and_retrieve("golden", {"variety": "Golden Cling", "sweetness": 9}),
        **make_handlers({}),
    )

    assert result == {"variety": "Golden Cling", "sweetness": 9}


def test_get_missing_peach_returns_none():
    """Proves fetching a non-existent peach returns None."""

    result = complete(fetch_only("nonexistent"), **make_handlers({}))

    assert result is None


def test_delete_removes_peach():
    """Proves deleting a peach means it can no longer be fetched."""

    result = complete(delete_then_fetch("elberta"), **make_handlers({}))

    assert result is None


def test_list_all_peaches():
    """Proves listing returns all stored peach IDs."""

    entries = [
        ("golden", {"variety": "Golden Cling"}),
        ("elberta", {"variety": "Elberta"}),
        ("donut", {"variety": "Donut"}),
    ]

    result = complete(save_many_then_list(entries), **make_handlers({}))

    assert sorted(result) == ["donut", "elberta", "golden"]


def test_overwrite_peach():
    """Proves saving to the same ID overwrites the previous entry."""

    result = complete(overwrite_peach("golden"), **make_handlers({}))

    assert result == {"sweetness": 10}
