"""Jobs around Genitopia: where you work, when, what it pays and the perks."""
from __future__ import annotations

from dataclasses import dataclass

from .model import Partner


@dataclass(frozen=True)
class Job:
    key: str
    title: str
    place: str            # room key where you clock in
    pay: int
    slots: tuple          # time slots you can work (0=morning .. 3=night)
    min_charm: int
    effects: dict
    perk: str


JOBS = {
    "office": Job("office", "Office assistant", "office", 60, (0, 1), 0,
                  {"energy": -18, "mood": -6, "hygiene": -6}, "Steady pay"),
    "cook": Job("cook", "Line cook", "diner", 50, (0, 1, 2), 0,
                {"energy": -16, "hygiene": -16, "fullness": 25}, "Free meal every shift"),
    "clerk": Job("clerk", "Pharmacy clerk", "pharmacy", 55, (0, 1), 25,
                 {"energy": -12, "mood": -3}, "A free condom every shift"),
    "apprentice": Job("apprentice", "Piercing apprentice", "studio", 40, (0, 1, 2), 30,
                      {"energy": -10, "mood": 4}, "Piercings 50% off"),
    "bartender": Job("bartender", "Bartender", "club", 40, (2, 3), 40,
                     {"energy": -18, "mood": 3, "hygiene": -8}, "Tips + flirty customers"),
    "concessions": Job("concessions", "Stadium concessions", "ballpark", 45, (0, 1, 2), 0,
                       {"energy": -16, "hygiene": -10}, "Bonus pay on game days"),
}
RAISE_EVERY = 6
RAISE = 10


def pay_for(gs) -> int:
    job = JOBS[gs.job]
    return job.pay + RAISE * (gs.shifts // RAISE_EVERY)


def apply(gs, key: str) -> str | None:
    job = JOBS[key]
    if gs.job == key:
        return "You already work here."
    if gs.charm < job.min_charm:
        return f"\"We'll call you.\" (Needs charm {job.min_charm}, you have {gs.charm}. Shower? Piercing?)"
    old = JOBS[gs.job].title if gs.job else None
    gs.job, gs.shifts = key, 0
    gs.say(f"You're hired as {job.title}! ${job.pay}/shift." + (f" You quit being {old.lower()}." if old else ""))
    return None


def work(gs) -> str | None:
    if not gs.job:
        return "You don't have a job. Ask around town!"
    job = JOBS[gs.job]
    if gs.slot not in job.slots:
        hours = ", ".join(("Morning", "Afternoon", "Evening", "Night")[s] for s in job.slots)
        return f"Your shifts are: {hours}."
    if gs.energy < 18:
        return "Too tired to work."
    from .baseball import is_game_day
    pay = pay_for(gs)
    extra = ""
    if job.key == "bartender":
        tips = gs.rng.randint(5, 45) + gs.charm // 4
        pay += tips
        extra = f" (incl. ${tips} tips)"
        if gs.rng.random() < 0.25:
            p = Partner.random(gs.rng, None if gs.show_me == "everyone" else gs.show_me)
            gs.add_match(p)
            extra += f" {p.name} left their number on a napkin!"
    elif job.key == "concessions" and is_game_day(gs):
        pay += 30
        extra = " (game day bonus!)"
    elif job.key == "clerk":
        gs.condoms += 1
        extra = " +1 free condom."
    elif job.key == "cook":
        extra = " You ate on the job."
    gs.money += pay
    gs.adjust(**job.effects)
    gs.shifts += 1
    gs.say(f"Worked a shift as {job.title.lower()}: +${pay}{extra}")
    if gs.shifts % RAISE_EVERY == 0:
        gs.say(f"You got a raise! Now ${pay_for(gs)}/shift.")
        gs.adjust(mood=10)
    gs.advance()
    return None


def quit_job(gs) -> str | None:
    if not gs.job:
        return "You're already unemployed."
    gs.say(f"You quit your job as {JOBS[gs.job].title.lower()}. Freedom! (And no income.)")
    gs.job, gs.shifts = None, 0
    return None
