from collections.abc import Generator
from dataclasses import dataclass
from typing import ClassVar, LiteralString

from orbis import Effect, complete


@dataclass
class EFetch(Effect[str]):
    tag: ClassVar[LiteralString] = "fetch"
    url: str


@dataclass
class User:
    id: int
    name: str


@dataclass
class Post:
    title: str


@dataclass
class Profile:
    user: User
    posts: list[Post]


def fetch_user(user_id: int) -> Generator[EFetch, str, User]:
    body = yield EFetch(f"/users/{user_id}")
    id_, name = body.split(":")

    return User(id=int(id_), name=name)


def fetch_posts(user_id: int) -> Generator[EFetch, str, list[Post]]:
    body = yield EFetch(f"/users/{user_id}/posts")

    return [Post(title=title) for title in body.split(",")]


def fetch_profile(user_id: int) -> Generator[EFetch, str, Profile]:
    user = yield from fetch_user(user_id)
    posts = yield from fetch_posts(user_id)

    return Profile(user=user, posts=posts)


RESPONSES: dict[str, str] = {
    "/users/1": "1:alice",
    "/users/1/posts": "hello world,effect systems",
}


def handle_fetch(effect: EFetch) -> str:
    return RESPONSES[effect.url]


def test_yield_from_composes_effectful_subprograms():
    """Proves `yield from` composes sub-programs; a single handler covers all their effects."""

    result = complete(fetch_profile(1), fetch=handle_fetch)

    assert result == Profile(
        user=User(id=1, name="alice"),
        posts=[Post(title="hello world"), Post(title="effect systems")],
    )
