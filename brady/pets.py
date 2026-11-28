"""Pets from Nuts & Eggs pet shop: a pair of testicles, a set of ovaries, or a pet sperm."""
from __future__ import annotations

from dataclasses import dataclass

PET_KINDS = {  # kind: (price, shop blurb)
    "testicles": (120, "A fuzzy, bouncy pair. Loyal. Always hang out together."),
    "ovaries": (120, "Two plump ovaries who wave their little tube-arms at you."),
    "sperm": (80, "A tiny swimmer. Fast, curious, never stops wiggling."),
}
DEFAULT_NAMES = {"testicles": "Bubbles & Squeak", "ovaries": "Ova & Eva", "sperm": "Zoom"}
MAX_PETS = 2
FOOD_PRICE = 6


@dataclass
class Pet:
    kind: str
    name: str
    fullness: float = 80
    happiness: float = 80


def buy(gs, kind: str) -> str | None:
    price = PET_KINDS[kind][0]
    if len(gs.pets) >= MAX_PETS:
        return f"Tad: \"Two pets is plenty! Your landlord would kill me.\""
    if gs.money < price:
        return f"That pet costs ${price}."
    gs.money -= price
    gs.pets.append(Pet(kind, DEFAULT_NAMES[kind]))
    gs.pet_food += 3
    gs.say(f"You adopted a pet {kind if kind != 'sperm' else 'sperm'}! Tad throws in 3 cans of food.")
    return None


def buy_food(gs) -> str | None:
    if gs.money < FOOD_PRICE:
        return f"Pet food is ${FOOD_PRICE}."
    gs.money -= FOOD_PRICE
    gs.pet_food += 3
    gs.say("Bought 3 cans of pet food.")
    return None


def feed(gs, i: int = 0) -> str | None:
    if not gs.pets:
        return "You don't have a pet."
    if gs.pet_food <= 0:
        return "No pet food left! Nuts & Eggs sells it."
    p = gs.pets[i]
    gs.pet_food -= 1
    p.fullness = 100
    gs.say(f"{p.name} gobbles up dinner. Happy noises.")
    return None


def play(gs, i: int = 0) -> str | None:
    if not gs.pets:
        return "You don't have a pet."
    p = gs.pets[i]
    p.happiness = 100
    gs.adjust(mood=8)
    trick = {"testicles": "bounce in perfect sync", "ovaries": "do a little wave with their tubes",
             "sperm": "zoom around your ankles at top speed"}[p.kind]
    gs.say(f"You play with {p.name}. They {trick}. Adorable.")
    return None


def tick(gs) -> None:
    for p in gs.pets:
        p.fullness = max(0, p.fullness - 5)
        p.happiness = max(0, p.happiness - 3)
        if p.fullness > 40 and p.happiness > 40:
            gs.adjust(mood=1)
        elif p.fullness == 0:
            gs.adjust(mood=-3)
            if gs.rng.random() < 0.2:
                gs.say(f"{p.name} is starving and giving you the saddest look.")
