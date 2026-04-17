
# Orbis

[![CI](https://github.com/rgrannell1/orbis/actions/workflows/ci.yml/badge.svg)](https://github.com/rgrannell1/orbis/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/rgrannell1/orbis/graph/badge.svg?token=BGMRKCfbCR)](https://codecov.io/gh/rgrannell1/orbis)

> All men who repeat a line from Shakespeare are William Shakespeare

Or, any method will do as long as it does the thing.

Orbis decouples what needs to be done from how it's done. It implements a Python-friendly subset of [algebraic effects](https://en.wikipedia.org/wiki/Effect_system), which is powerful enough for my own uses.

Some programs emit events (e.g `yield Event`), to signal something to outside handler functions. Orbis allows those handlers to respond back.

```python
from dataclasses import dataclass
from typing import ClassVar, Generator
from orbis import Effect, Event, complete


@dataclass
class EAsk(Effect[str]):
    tag: ClassVar[str] = "ask"
    question: str


@dataclass
class ESpeak(Event):
    tag: ClassVar[str] = "speak"
    line: str


def bridge_of_death() -> Generator[EAsk | ESpeak, str, str]:
    name   = yield EAsk("What is your name?")
    _quest = yield EAsk("What is your quest?")
    colour = yield EAsk("What is your favourite colour?")

    if colour.lower() == "blue":
        yield ESpeak(f"Right. Off you go, {name}.")
        return "crossed"
    else:
        yield ESpeak("Auuuuuugh!")
        return "gorge"


result = complete(
    bridge_of_death(),
    ask=lambda effect: input(f"{effect.question} "),
    speak=lambda effect: print(effect.line),
)
```

This event-like effect pattern allows aspects of a program to be decoupled; we want to do a thing, but another part of the program may decide how. This is analogous to dependency-injection, higher-order function usage, request-response, or IPC.

Why bother?
- Type signatures document logging, database calls, and other aspects of a program
- Non-OOP dependency injection; program against interfaces rather than concrete implementations
- Clean implementation of custom control-flow mechanisms & state-machines
- No mocks in testing is a benefit
- Nicer than monads

## Constructs

Effect systems are composed of effects (requests to do something), and handlers (how they're done).

### Effects - Communicate & request

Effects are like events that can receive responses from their handler; or alternatively, like function calls that cross the generator's borders. This gives the benefit of being able to show at the type-level you'd logged, fetched a resource, or other actions normally hidden as system internals.

```python
def get_user(id: int) -> Generator[EGetUser, User, User]:
    user = yield EGetUser(id)
    return user
```

It is more powerful than just function-calls-with-extra-steps; since we're using generators we suspend and resume functions and can wire in custom control flow using Effects. For example, you would recursively search across generators and yield an early suspension event on receiving a match. Many control flow operators can be wired in using an effect system, if needed.

```python
@dataclass
class EFound(Effect[Never]):
    tag: ClassVar[str] = "found"
    value: Any

class Found(Exception):
    def __init__(self, value):
        self.value = value

def search(tree) -> Generator[EFound, Never, None]:
    if isinstance(tree, int) and tree > 100:
        yield EFound(tree)

    elif isinstance(tree, list):
        for subtree in tree:
            yield from search(subtree)

huge_tree = [[1, [2, 150]], [3, [4, [5]]]]

def handle_found(effect: EFound) -> Never:
    raise Found(effect.value)

try:
    complete(search(huge_tree), found=handle_found)
except Found as find:
    result = find.value
```

Events don't receive responses; they're simply modelled as `Effect[None]` and are used to broadcast information to a handler (that can then multicast, store, print, whatever you chose).

### Handlers - Listen & react

Handlers are just normal generators; they're registered to listen for an effect, and upon receiving it they return a value, raise an error, or yield their own effects.

## Composition

## Build

```sh
rs install   # install dependencies
rs test      # run tests
rs lint      # lint
rs format    # format
```

## Licence

Copyright © 2026 Róisín Grannell

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
