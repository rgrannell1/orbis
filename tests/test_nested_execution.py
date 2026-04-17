
from functools import partial
from typing import Generator
from orbis import Effect, OnEffect


class ERequest(Effect[str]):
  tag = "request"


class ERespond(Effect[None]):
  tag = "respond"

  def __init__(self, body: str):
    self.body = body


class ELog(Effect[None]):
  tag = "log"

  def __init__(self, message: str):
    self.message = message


def fake_server() -> Generator[ERequest | ERespond | ELog, object, str]:
  """An effectful program simulating a server."""

  path = yield ERequest()

  yield ELog(f"request: {path}")
  yield ERespond(f"200 OK {path}")
  yield ELog("response sent")

  return "done"


def handle_request(effect: ERequest) -> str:
  return "/hello"


def handle_respond(responses: list[str], effect: ERespond) -> None:
  responses.append(effect.body)


def handle_log(log_lines: list[str], effect: ELog) -> None:
  log_lines.append(effect.message)


def with_server_handlers(
  responses: list[str],
  gen: Generator[ERequest | ERespond | ELog, object, str],
) -> Generator[ERequest | ERespond | ELog, object, str]:
  """Handles ERequest and ERespond, letting ELog bubble."""

  return OnEffect({"request": handle_request, "respond": partial(handle_respond, responses)}).run(gen)


def test_log_handled_by_downstream_handler():
  """Proves handlers can nest, and pass effects downwards if unconsumed."""

  log_lines: list[str] = []
  responses: list[str] = []

  result = OnEffect({"log": partial(handle_log, log_lines)}).complete(with_server_handlers(responses, fake_server()))

  assert result == "done"
  assert responses == ["200 OK /hello"]
  assert log_lines == ["request: /hello", "response sent"]
