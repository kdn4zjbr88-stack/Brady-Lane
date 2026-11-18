"""Player actions. Each returns None on success or a string explaining why it can't be done."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .model import GameState, Partner

CONDOM_PACK_PRICE = 15
CONDOM_PACK_SIZE = 3
MEAL_PRICE = 12
PARTY_PRICE = 30
CLINIC_PRICE = 50
WORK_PAY = 60


def eat(gs: GameState) -> str | None:
    if gs.money < MEAL_PRICE:
        return f"You need ${MEAL_PRICE} to eat."
    gs.money -= MEAL_PRICE
    gs.adjust(fullness=40, mood=5, health=2)
    gs.say("You grabbed a solid meal. Nom.")
    gs.advance()
    return None


def shower(gs: GameState) -> str | None:
    gs.hygiene = 100
    gs.adjust(mood=6)
    gs.say("Fresh and clean! Squeaky.")
    gs.advance()
    return None


def sleep(gs: GameState) -> str | None:
    remaining = 4 - gs.slot
    gs.advance(remaining)  # sleep through to next morning
    if gs.game_over:
        return None
    gs.energy = 100
    gs.adjust(health=8, mood=5, fullness=10)  # partially offsets decay while asleep
    gs.say(f"You slept well. Good morning, day {gs.day}!")
    return None


def work(gs: GameState) -> str | None:
    if gs.time_name == "Night":
        return "Nobody's hiring at night. Try sleeping or partying."
    if gs.energy < 20:
        return "Too tired to work."
    gs.money += WORK_PAY
    gs.adjust(energy=-18, mood=-6, hygiene=-8)
    gs.say(f"You put in a shift and earned ${WORK_PAY}.")
    gs.advance()
    return None


def party(gs: GameState) -> str | None:
    if gs.time_name not in ("Evening", "Night"):
        return "Parties start in the evening."
    if gs.money < PARTY_PRICE:
        return f"You need ${PARTY_PRICE} to go out."
    if gs.energy < 20:
        return "Too tired to party."
    gs.money -= PARTY_PRICE
    gs.adjust(mood=22, energy=-22, hygiene=-12, fullness=-5)
    met = [Partner.random(gs.rng) for _ in range(gs.rng.randint(1, 2))]
    gs.partners.extend(met)
    del gs.partners[:-6]  # only remember recent contacts
    names = ", ".join(f"{p.name} ({p.age}, {p.vibe})" for p in met)
    gs.say(f"Great night out! You swapped numbers with {names}.")
    gs.advance()
    return None


def buy_condoms(gs: GameState) -> str | None:
    if gs.money < CONDOM_PACK_PRICE:
        return f"Condoms cost ${CONDOM_PACK_PRICE}."
    gs.money -= CONDOM_PACK_PRICE
    gs.condoms += CONDOM_PACK_SIZE
    gs.say(f"Bought a {CONDOM_PACK_SIZE}-pack of condoms. Smart move.")
    return None  # quick errand, takes no time


def clinic(gs: GameState) -> str | None:
    if gs.time_name == "Night":
        return "The clinic is closed at night."
    if gs.money < CLINIC_PRICE:
        return f"A clinic visit costs ${CLINIC_PRICE}."
    gs.money -= CLINIC_PRICE
    if gs.infection:
        gs.say(f"Diagnosed: {gs.infection}. Treated! You feel better already.")
        gs.infection = None
        gs.adjust(health=15, mood=10)
    else:
        gs.say("Tested negative for everything. Clean bill of health!")
        gs.adjust(mood=8)
    gs.advance()
    return None


def can_hook_up(gs: GameState) -> str | None:
    if not gs.partners:
        return "You don't know anyone yet. Go out partying to meet people."
    if gs.energy < 15:
        return "Too tired for that right now."
    return None


def hook_up(gs: GameState, partner: Partner, protected: bool) -> str | None:
    blocked = can_hook_up(gs)
    if blocked:
        return blocked
    if protected and gs.condoms <= 0:
        return "You're out of condoms. Buy some first."

    gs.total_hookups += 1
    partner.times += 1
    fun = 15 + 25 * partner.chemistry
    gs.adjust(mood=fun, energy=-15, hygiene=-20)

    if protected:
        gs.condoms -= 1
        gs.protected_hookups += 1
        risk = partner.sti_risk * 0.05
        gs.say(f"You spent a fun, safe night with {partner.name}.")
    else:
        risk = partner.sti_risk
        gs.say(f"You spent a wild night with {partner.name}... no protection.")
        if gs.scare_days == 0 and gs.rng.random() < 0.2:
            gs.scare_days = 3
            who = "you might be" if gs.character.kind == "vagina" else f"{partner.name} might be"
            gs.say(f"Uh oh, a period is late: {who} pregnant. Anxious days ahead.")
            gs.adjust(mood=-15)

    if gs.infection is None and gs.rng.random() < risk:
        gs._infect(gs.rng.choice(["Chlamydia", "Gonorrhea", "Herpes flare-up", "Trichomoniasis"]))
        gs.say("A few days later something feels off... maybe visit the clinic.")

    gs.advance()
    return None


@dataclass(frozen=True)
class Action:
    key: str
    label: str
    func: Callable[[GameState], str | None]
    hint: str


ACTIONS: list[Action] = [
    Action("eat", "Eat", eat, f"${MEAL_PRICE} · +Fullness"),
    Action("shower", "Shower", shower, "Hygiene to 100"),
    Action("sleep", "Sleep", sleep, "Rest till morning"),
    Action("work", "Work", work, f"+${WORK_PAY} · -Energy"),
    Action("party", "Party", party, f"${PARTY_PRICE} · Meet people"),
    Action("condoms", "Buy condoms", buy_condoms, f"${CONDOM_PACK_PRICE} for {CONDOM_PACK_SIZE}"),
    Action("clinic", "Clinic", clinic, f"${CLINIC_PRICE} · Test & treat"),
]
