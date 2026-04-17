
# Orbis

[![CI](https://github.com/rgrannell1/orbis/actions/workflows/ci.yml/badge.svg)](https://github.com/rgrannell1/orbis/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/rgrannell1/orbis/graph/badge.svg?token=BGMRKCfbCR)](https://codecov.io/gh/rgrannell1/orbis)

> All men who repeat a line from Shakespeare are William Shakespeare

Orbis decouples what needs to be done from how it's done. It implements a Python-friendly subset of [algebraic effect](https://en.wikipedia.org/wiki/Effect_system), which is powerful enough for my own uses.

Some programs emit events (e.g `yield Event`), to signal something to outside handler functions. Orbis allows those handlers to respond back.

```python
from dataclasses import dataclass
from typing import ClassVar, Generator
from orbis import Effect, Event, OnEffect


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


result = OnEffect({
    "ask":   lambda effect: input(f"{effect.question} "),
    "speak": lambda effect: print(effect.line),
}).complete(bridge_of_death())
```

This event-like effect pattern allows aspects of a program to be decoupled; we want to do a thing, but another part of the program may decide how. This is analagous to dependency-injection, higher-order function usage, request-response, or IPC.

Why bother?
- Type signatures document logging, database calls, and other aspects of a program
- Non-OOP dependency injection
- Clean implementation of custom control-flow mechanisms & state-machines
- No mocks in testing is a benefit
- Nicer than monads

## Build

```sh
rs install   # install dependencies
rs run       # run the project
rs test      # run tests
rs lint      # lint
rs format    # format
```

## Licence

Copyright © 2026 Róisín Grannell

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
