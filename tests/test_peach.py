"""Tests for a peach repository — demonstrating the repository pattern with effects."""

from dataclasses import dataclass
from collections.abc import Generator
from functools import partial
from operator import attrgetter
from typing import ClassVar

from orbis import Effect, Event, complete


@dataclass
class Peach:
    id: int
    variety: str
    weight_grams: int


@dataclass
class EStorePeach(Event):
    tag: ClassVar[LiteralString] = "store_peach"
    peach: Peach


@dataclass
class EFetchPeach(Effect[Peach | None]):
    tag: ClassVar[LiteralString] = "fetch_peach"
    peach_id: int


class EListPeaches(Effect[list[Peach]]):
    tag: ClassVar[LiteralString] = "list_peaches"


@dataclass
class EDeletePeach(Effect[bool]):
    tag: ClassVar[LiteralString] = "delete_peach"
    peach_id: int


PeachRepoEffect = EStorePeach | EFetchPeach | EListPeaches | EDeletePeach

# a golden peach
GOLDEN = Peach(id=1, variety="Golden", weight_grams=150)

# an empress peach
EMPRESS = Peach(id=2, variety="Empress", weight_grams=180)


def store_peach(peach: Peach) -> Generator[EStorePeach, None, None]:
    yield EStorePeach(peach)


def fetch_peach(peach_id: int) -> Generator[EFetchPeach, Peach | None, Peach | None]:
    return (yield EFetchPeach(peach_id))


def list_peaches() -> Generator[EListPeaches, list[Peach], list[Peach]]:
    return (yield EListPeaches())


def delete_peach(peach_id: int) -> Generator[EDeletePeach, bool, bool]:
    return (yield EDeletePeach(peach_id))


def store_and_fetch_golden() -> Generator[PeachRepoEffect, object, Peach | None]:
    yield from store_peach(GOLDEN)
    return (yield from fetch_peach(GOLDEN.id))


def store_golden_and_empress_then_list() -> Generator[PeachRepoEffect, object, list[Peach]]:
    yield from store_peach(GOLDEN)
    yield from store_peach(EMPRESS)
    return (yield from list_peaches())


def store_then_delete_golden() -> Generator[PeachRepoEffect, object, bool]:
    yield from store_peach(GOLDEN)
    return (yield from delete_peach(GOLDEN.id))


# In-memory repository handlers

def handle_store(store: dict[int, Peach], effect: EStorePeach) -> None:
    store[effect.peach.id] = effect.peach


def handle_fetch(store: dict[int, Peach], effect: EFetchPeach) -> Peach | None:
    return store.get(effect.peach_id)


def handle_list(store: dict[int, Peach], effect: EListPeaches) -> list[Peach]:
    return list(store.values())


def handle_delete(store: dict[int, Peach], effect: EDeletePeach) -> bool:
    if effect.peach_id not in store:
        return False
    del store[effect.peach_id]
    return True


def make_handlers(store: dict[int, Peach]) -> dict:
    return {
        "store_peach": partial(handle_store, store),
        "fetch_peach": partial(handle_fetch, store),
        "list_peaches": partial(handle_list, store),
        "delete_peach": partial(handle_delete, store),
    }


def test_store_and_fetch():
    """Proves a stored peach can be retrieved by id."""

    result = complete(store_and_fetch_golden(), **make_handlers({}))

    assert result == GOLDEN


def test_fetch_missing_returns_none():
    """Proves fetching a non-existent peach id returns None."""

    result = complete(fetch_peach(99), **make_handlers({}))

    assert result is None


def test_list_peaches():
    """Proves listing returns all stored peaches."""

    result = complete(store_golden_and_empress_then_list(), **make_handlers({}))

    assert sorted(result, key=attrgetter("id")) == [GOLDEN, EMPRESS]


def test_delete_existing_returns_true():
    """Proves deleting an existing peach returns True and removes it."""

    store: dict[int, Peach] = {}
    handlers = make_handlers(store)

    deleted = complete(store_then_delete_golden(), **handlers)
    remaining = complete(list_peaches(), **handlers)

    assert deleted is True
    assert remaining == []


def test_delete_missing_returns_false():
    """Proves deleting a non-existent peach id returns False."""

    result = complete(delete_peach(99), **make_handlers({}))

    assert result is False
