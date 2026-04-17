
from typing import Any, Generator
from orbis import Effect, Event, OnEffect


class EFetch(Effect[str]):
  tag = "fetch"

  def __init__(self, url: str):
    self.url = url


class ELog(Event):
  tag = "log"

  def __init__(self, message: str):
    self.message = message


def fetch_user(user_id: int) -> Generator[EFetch | ELog, str, dict]:
  yield ELog(f"fetching /users/{user_id}")
  body = yield EFetch(f"/users/{user_id}")
  return {"id": user_id, "name": body}


def with_http(gen: Generator[Any, Any, Any]) -> Generator[Any, Any, Any]:
  return OnEffect({"fetch": lambda effect: "alice"}).run(gen)


def main() -> Generator[ELog, None, str]:
  yield ELog("starting")
  user = yield from with_http(fetch_user(1))
  yield ELog(f"got user: {user['name']}")
  return user["name"]


def test_logs_propagate_from_inner_workflow():
  """Proves ELog effects bubble out of inner handlers specifically."""

  logs: list[str] = []

  result = OnEffect({"log": lambda effect: logs.append(effect.message)}).complete(main())

  assert result == "alice"
  assert logs == ["starting", "fetching /users/1", "got user: alice"]
