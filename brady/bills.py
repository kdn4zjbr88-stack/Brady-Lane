"""Weekly bills. Pay them from the phone. Skip them and things get shut off."""
from __future__ import annotations

from dataclasses import dataclass

LATE_FEE = 15


@dataclass
class Bill:
    key: str
    name: str
    base: int
    due_day: int
    late: bool = False

    def amount(self, gs) -> int:
        extra = 6 * len(gs.upgrades) if self.key == "utilities" else 0
        base = self.base // 2 if self.key == "rent" and gs.relationship == "married" else self.base
        return base + extra + (LATE_FEE if self.late else 0)

    def overdue(self, gs) -> int:
        return max(0, gs.day - self.due_day)


def starting_bills() -> list[Bill]:
    return [Bill("rent", "Rent", 140, 7), Bill("utilities", "Power & water", 35, 7),
            Bill("phone", "Phone plan", 25, 7)]


def pay(gs, key: str) -> str | None:
    bill = next(b for b in gs.bills if b.key == key)
    amt = bill.amount(gs)
    if gs.money < amt:
        return f"You need ${amt} to pay {bill.name.lower()}."
    gs.money -= amt
    bill.due_day += 7
    bill.late = False
    if key == "utilities" and gs.utilities_off:
        gs.utilities_off = False
        gs.say("The power and water come back on. Hot showers, baby!")
    if key == "phone" and gs.phone_off:
        gs.phone_off = False
        gs.say("Your phone works again. 47 unread messages.")
    gs.say(f"Paid {bill.name.lower()}: ${amt}. Next one due day {bill.due_day}.")
    return None


def due_soon(gs) -> list[Bill]:
    return [b for b in gs.bills if b.due_day - gs.day <= 2]


def new_day(gs) -> None:
    for b in gs.bills:
        if b.due_day - gs.day == 2:
            gs.say(f"Reminder: {b.name.lower()} (${b.amount(gs)}) is due in 2 days.")
        over = b.overdue(gs)
        if over <= 0:
            continue
        if not b.late:
            b.late = True
            gs.say(f"{b.name} is overdue! A ${LATE_FEE} late fee was added.")
        gs.adjust(mood=-5)
        if b.key == "utilities" and over >= 2 and not gs.utilities_off:
            gs.utilities_off = True
            gs.say("The power and water got shut off. No showers or cooking at home until you pay.")
        if b.key == "phone" and over >= 2 and not gs.phone_off:
            gs.phone_off = True
            gs.say("Your phone got cut off. No Spark until you pay the bill.")
        if b.key == "rent":
            if over == 2:
                gs.say("Your landlord left a note: \"Pay rent in 2 days or you're OUT.\"")
            if over >= 4 and not gs.game_over:
                gs.game_over = True
                gs.end_reason = "Evicted! You couldn't pay rent. Genitopia is a tough town."
