
from functools import partial
from typing import Generator
from orbis import Effect, on_effect, complete


class Request(Effect[str]):
  tag = "request"


class Respond(Effect[None]):
  tag = "respond"

  def __init__(self, body: str):
    self.body = body


class Log(Effect[None]):
  tag = "log"

  def __init__(self, message: str):
    self.message = message


def fake_server() -> Generator[Request | Respond | Log, object, str]:
  """An effectful program simulating a server."""

  path = yield Request()

  yield Log(f"request: {path}")
  yield Respond(f"200 OK {path}")
  yield Log("response sent")

  return "done"


def handle_request(effect: Request) -> str:
  return "/hello"


def handle_respond(responses: list[str], effect: Respond) -> None:
  responses.append(effect.body)


def handle_log(log_lines: list[str], effect: Log) -> None:
  log_lines.append(effect.message)


def with_server_handlers(
  responses: list[str],
  gen: Generator[Request | Respond | Log, object, str],
) -> Generator[Request | Respond | Log, object, str]:
  """Handles Request and Respond, letting Log bubble."""

  return on_effect(request=handle_request, respond=partial(handle_respond, responses)).run(gen)


def test_log_handled_by_downstream_handler():
  """Proves handlers can nest, and pass effects downwards if unconsumed."""

  log_lines: list[str] = []
  responses: list[str] = []

  result = complete(on_effect(log=partial(handle_log, log_lines)).run(with_server_handlers(responses, fake_server())))

  assert result == "done"
  assert responses == ["200 OK /hello"]
  assert log_lines == ["request: /hello", "response sent"]
