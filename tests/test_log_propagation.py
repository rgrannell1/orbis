"""Tests for effect propagation across nested handle boundaries."""

from collections.abc import Generator
from dataclasses import dataclass
from functools import partial
from typing import Any, ClassVar, LiteralString

from orbis import Effect, Event, complete, handle


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[LiteralString] = "fetch"
    url: str


@dataclass
class ELog(Event):
    tag: ClassVar[LiteralString] = "log"
    message: str


def fetch_user(user_id: int) -> Generator[EFetch | ELog, str, dict]:
    yield ELog(f"fetching /users/{user_id}")
    body = yield EFetch(f"/users/{user_id}")
    return {"id": user_id, "name": body}


def _return_alice(_) -> str:
    return "alice"


def with_http(gen: Generator[Any, Any, Any]) -> Generator[Any, Any, Any]:
    return handle(gen, fetch=_return_alice)


def main() -> Generator[ELog, None, str]:
    yield ELog("starting")
    user = yield from with_http(fetch_user(1))
    yield ELog(f"got user: {user['name']}")
    return user["name"]


def _record_message(target: list, effect: ELog) -> None:
    target.append(effect.message)


def test_logs_propagate_from_inner_workflow():
    """Proves ELog effects bubble out of inner handlers specifically."""

    logs: list[str] = []

    result = complete(main(), log=partial(_record_message, logs))

    assert result == "alice"
    assert logs == ["starting", "fetching /users/1", "got user: alice"]
