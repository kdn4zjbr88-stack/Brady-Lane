"""Clothes & accessories from Birthday Suits boutique (they show on your character), plus the gym."""
from __future__ import annotations

ACCESSORIES = {  # key: (label, charm, price)
    "sunglasses": ("Sunglasses", 4, 60),
    "cowboyhat": ("Cowboy hat", 5, 80),
    "flowercrown": ("Flower crown", 4, 50),
    "bowtie": ("Bow tie", 3, 40),
    "goldchain": ("Gold chain", 8, 150),
}
ACCESSORIES = {k: (v[0], v[1], v[2]) for k, v in ACCESSORIES.items()}
GYM_PRICE = 10


def buy_or_wear(gs, key: str) -> str | None:
    label, _, price = ACCESSORIES[key]
    if key in gs.wardrobe:
        gs.wearing = "" if gs.wearing == key else key
        gs.character.accessory = gs.wearing
        gs.say(f"You {'put on' if gs.wearing else 'take off'} your {label.lower()}.")
        return None
    if gs.money < price:
        return f"The {label.lower()} costs ${price}."
    gs.money -= price
    gs.wardrobe.append(key)
    gs.wearing = key
    gs.character.accessory = key
    gs.adjust(mood=8)
    gs.say(f"You buy a {label.lower()} and wear it out of the store. Looking sharp!")
    return None


def gym_workout(gs) -> str | None:
    free = gs.job == "trainer"
    if not free and gs.money < GYM_PRICE:
        return f"A gym day pass is ${GYM_PRICE}."
    if gs.energy < 20:
        return "Too tired to work out."
    if not free:
        gs.money -= GYM_PRICE
    gs.adjust(energy=-20, hygiene=-22, mood=10, health=5)
    gs.fitness = min(20, gs.fitness + 2)
    gs.say(f"You lift, you sweat, Brick yells encouragement. Fitness {gs.fitness}/20.")
    gs.advance()
    return None
