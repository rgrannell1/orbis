from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, ClassVar, LiteralString

from orbis import Effect, Event, complete

# --- Vending Machine Effects ---


@dataclass
class EDisplay(Event):
    tag: ClassVar[LiteralString] = "display"
    message: str


class EInsertCoin(Effect[int]):
    tag = "insert_coin"


@dataclass
class ESelectItem(Effect[str | None]):
    tag: ClassVar[LiteralString] = "select_item"
    balance: int


@dataclass
class EDispense(Event):
    tag: ClassVar[LiteralString] = "dispense"
    item_id: str


@dataclass
class EReturnChange(Event):
    tag: ClassVar[LiteralString] = "return_change"
    amount: int


# --- State sub-generators ---
VendingMachingEffect = EDisplay | EInsertCoin | ESelectItem | EDispense | EReturnChange

PRICES: dict[str, int] = {
    "crisps": 50,
    "cola": 75,
    "water": 40,
}


def idle() -> Generator[EDisplay | EInsertCoin, int, int]:
    yield EDisplay("insert coins to begin")
    return (yield EInsertCoin())


def funded(
    balance: int,
    prices: dict[str, int],
) -> Generator[EDisplay | ESelectItem, str | None, tuple[str | None, int]]:
    yield EDisplay(f"balance: {balance}p")
    selection = yield ESelectItem(balance)

    if selection is None:
        return (None, balance)

    price = prices.get(selection)

    if price is None:
        yield EDisplay(f"unknown item: {selection}")
        return (None, balance)

    if price > balance:
        yield EDisplay(f"need {price - balance}p more for {selection}")
        return (None, balance)

    return (selection, balance - price)


def vending_machine(
    prices: dict[str, int],
    transactions: int = 1,
) -> Generator[VendingMachingEffect, Any, None]:
    for _ in range(transactions):
        balance = yield from idle()

        while balance > 0:
            item, balance = yield from funded(balance, prices)

            if item:
                yield EDispense(item)
            else:
                yield EReturnChange(balance)
                balance = 0


# --- Handler factories ---


def scripted_coins(*amounts: int):
    coins = iter(amounts)

    def handle(effect: EInsertCoin) -> int:
        return next(coins)

    return handle


def scripted_selections(*items: str | None):
    selections = iter(items)

    def handle(effect: ESelectItem) -> str | None:
        return next(selections)

    return handle


def recording_display(log: list[str]):
    def handle(effect: EDisplay) -> None:
        log.append(effect.message)

    return handle


def recording_dispense(log: list[str]):
    def handle(effect: EDispense) -> None:
        log.append(effect.item_id)

    return handle


def recording_change(log: list[int]):
    def handle(effect: EReturnChange) -> None:
        log.append(effect.amount)

    return handle


# --- Tests ---


def run(transactions: int, coins: tuple[int, ...], selections: tuple[str | None, ...]):
    dispensed: list[str] = []
    change: list[int] = []

    complete(
        vending_machine(PRICES, transactions=transactions),
        display=recording_display([]),
        insert_coin=scripted_coins(*coins),
        select_item=scripted_selections(*selections),
        dispense=recording_dispense(dispensed),
        return_change=recording_change(change),
    )

    return dispensed, change


def test_exact_change_no_change_returned():
    """Proves state-machines flows as expected"""

    dispensed, change = run(1, coins=(50,), selections=("crisps",))

    assert dispensed == ["crisps"]
    assert change == []


def test_overpay_returns_change():
    """Proves state-machines flows as expected"""

    dispensed, change = run(1, coins=(100,), selections=("crisps", None))

    assert dispensed == ["crisps"]
    assert change == [50]


def test_cancel_returns_full_amount():
    """Proves state-machines flows as expected"""

    dispensed, change = run(1, coins=(50,), selections=(None,))

    assert dispensed == []
    assert change == [50]


def test_insufficient_funds_then_cancel():
    """Proves state-machines flows as expected"""

    messages: list[str] = []
    dispensed: list[str] = []
    change: list[int] = []

    complete(
        vending_machine(PRICES, transactions=1),
        display=recording_display(messages),
        insert_coin=scripted_coins(30),
        select_item=scripted_selections("crisps", None),
        dispense=recording_dispense(dispensed),
        return_change=recording_change(change),
    )

    assert dispensed == []
    assert change == [30]
    assert any("need 20p more" in mesg for mesg in messages)


def test_multiple_items_single_session():
    """Proves state-machines flows as expected"""

    dispensed, change = run(1, coins=(100,), selections=("water", "water", None))

    assert dispensed == ["water", "water"]
    assert change == [20]


def test_two_separate_transactions():
    """Proves state-machines flows as expected"""

    dispensed, change = run(2, coins=(50, 75), selections=("crisps", "cola"))

    assert dispensed == ["crisps", "cola"]
    assert change == []
