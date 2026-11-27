"""House upgrades sold at Screw & Nail hardware."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Upgrade:
    key: str
    name: str
    price: int
    blurb: str


UPGRADES = {
    "bed": Upgrade("bed", "Luxury king bed", 200, "Sleep restores more health & mood"),
    "shower": Upgrade("shower", "Rain shower", 150, "Showers give a mood boost"),
    "kitchen": Upgrade("kitchen", "Chef's kitchen", 160, "Cook cheap, big meals at home"),
    "tv": Upgrade("tv", "Giant TV", 180, "Watch TV & Ballers games at home"),
    "gym": Upgrade("gym", "Home gym", 220, "Work out for permanent charm"),
    "hottub": Upgrade("hottub", "Hot tub", 300, "Huge relaxation; dates love it"),
    "nursery": Upgrade("nursery", "Dreamy nursery", 140, "Baby stays happy in the crib"),
}


def buy(gs, key: str) -> str | None:
    u = UPGRADES[key]
    if key in gs.upgrades:
        return "You already own that."
    if gs.money < u.price:
        return f"The {u.name.lower()} costs ${u.price}."
    gs.money -= u.price
    gs.upgrades.append(key)
    gs.adjust(mood=12)
    gs.say(f"Mandy delivers your {u.name.lower()}! Home sweet home. (Utilities go up a little.)")
    return None


# ---- things you can do with them at home ---------------------------------------
def cook(gs) -> str | None:
    if gs.utilities_off:
        return "The power is off. Pay your utilities bill."
    if gs.money < 4:
        return "Groceries cost $4."
    gs.money -= 4
    gs.adjust(fullness=45, mood=6, health=3)
    dish = gs.rng.choice(["garlic pasta", "a stir-fry", "tacos from scratch", "a fancy omelette"])
    gs.say(f"You cook {dish} in your shiny kitchen. Chef's kiss.")
    if gs.craving and gs.is_carrier:
        gs.say(f"...and you whip up {gs.craving} on the side. Craving: satisfied.")
        gs.craving = None
        gs.adjust(mood=15)
    gs.advance()
    return None


def watch_tv(gs) -> str | None:
    if gs.utilities_off:
        return "The power is off. Pay your utilities bill."
    from .baseball import is_game_day
    if is_game_day(gs) and gs.slot == 2:
        gs.say("You watch the Ballers game on the big screen and yell at the umpire.")
        gs.adjust(mood=14)
    else:
        show = gs.rng.choice(["a trashy dating show", "a nature documentary about bonobos",
                              "a cooking competition", "Genitopia local news"])
        gs.say(f"You binge {show}. Brain off. Bliss.")
        gs.adjust(mood=10, energy=4)
    gs.advance()
    return None


def workout(gs) -> str | None:
    if gs.energy < 20:
        return "Too tired to work out."
    gs.adjust(energy=-18, hygiene=-20, mood=8, health=4)
    gs.fitness = min(20, gs.fitness + 2)
    gs.say(f"You crush a workout. Looking good! (Fitness {gs.fitness}/20 adds to charm)")
    gs.advance()
    return None


def hot_tub(gs) -> str | None:
    if gs.utilities_off:
        return "The power is off. Pay your utilities bill."
    gs.adjust(mood=20, energy=10, hygiene=5)
    gs.say("You sink into the hot tub. Every muscle melts.")
    gs.advance()
    return None
