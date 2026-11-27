"""Menstrual cycle for the vagina character (compressed so it matters in a 30-day game)."""
from __future__ import annotations

CYCLE_LEN = 10
# cycle day -> phase
PHASES = {1: "period", 2: "period", 3: "period", 4: "follicular", 5: "fertile", 6: "fertile",
          7: "fertile", 8: "luteal", 9: "pms", 10: "pms"}
PHASE_INFO = {
    "period": ("Period", (220, 70, 90)),
    "follicular": ("Rising energy", (240, 170, 120)),
    "fertile": ("Fertile window", (110, 190, 140)),
    "luteal": ("Luteal", (170, 150, 220)),
    "pms": ("PMS", (230, 140, 190)),
}
# multiplies the hidden pregnancy risk of unprotected sex
FERTILITY = {"period": 0.25, "follicular": 0.6, "fertile": 1.8, "luteal": 0.5, "pms": 0.3}


def has_cycle(gs) -> bool:
    return gs.character.kind == "vagina" and gs.conception is None


def phase(gs) -> str | None:
    return PHASES[gs.cycle_day] if has_cycle(gs) else None


def fertility(gs) -> float:
    p = phase(gs)
    return FERTILITY[p] if p else 1.0


def days_until_period(gs) -> int:
    return (CYCLE_LEN - gs.cycle_day + 1) % CYCLE_LEN


def new_day(gs) -> None:
    if not has_cycle(gs):
        return
    gs.cycle_day = gs.cycle_day % CYCLE_LEN + 1
    gs.leaked_today = False
    p = PHASES[gs.cycle_day]
    if gs.cycle_day == 1:
        gs.say("Your period started. Cramps incoming. Hope you've got supplies!")
    elif gs.cycle_day == 5:
        gs.say("You're feeling glowy and confident today. (Fertile window: extra careful!)")
    elif p == "pms" and gs.cycle_day == 9:
        gs.say("PMS mode: everything is annoying and you want ALL the chocolate.")
        if gs.craving is None:
            gs.craving = "a giant chocolate bar"


def tick(gs) -> None:
    p = phase(gs)
    if p == "period":
        if gs.period_supplies > 0:
            gs.period_supplies -= 1
        elif not gs.leaked_today:
            gs.leaked_today = True
            gs.adjust(hygiene=-15, mood=-8)
            gs.say("You ran out of pads & tampons and... leaked. Ugh. Pharmacy, now.")
        else:
            gs.adjust(hygiene=-5)
        if gs.rng.random() < 0.3:
            if gs.painkillers > 0:
                gs.painkillers -= 1
                gs.say("Cramps hit. You pop a painkiller. Better.")
            else:
                gs.adjust(energy=-6, mood=-6)
                gs.say("Cramps! You curl up for a bit. Painkillers would help.")
    elif p == "pms":
        gs.adjust(mood=-2)


def charm_bonus(gs) -> int:
    return 6 if phase(gs) == "fertile" else 0
