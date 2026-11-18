"""Random happenings around Genitopia. Each event sits somewhere in town for a few time slots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .model import GameState, Partner

# Free spots on sidewalks / lawns where an event can appear (town coordinates).
EVENT_SPOTS = [(660, 700), (1100, 700), (1460, 700), (1960, 700), (2480, 920),
               (1140, 930), (700, 920), (1450, 1400), (2200, 920), (120, 930)]


@dataclass
class TownEvent:
    key: str
    title: str
    x: int
    y: int
    slots_left: int


@dataclass
class EventOption:
    label: str
    sub: str
    fn: Callable[[GameState], str | None] | None


# ---- event catalogue --------------------------------------------------------
# key: (title, intro text shown in the pop-up, min slot, max slot, duration in slots)
CATALOGUE = {
    "busker": ("Street musician", "A saxophonist is playing a very sultry song.", 0, 3, 3),
    "tacotruck": ("Taco truck", "\"Los Tacos Calientes\" smells incredible.", 0, 3, 3),
    "wallet": ("Lost wallet", "A fat wallet is lying on the sidewalk...", 0, 3, 4),
    "giveaway": ("Free condom stand", "Nurse Ova is handing out free condoms. \"Wrap it up, Genitopia!\"", 0, 1, 2),
    "blockparty": ("Block party", "Speakers, string lights and a crowd dancing in the street.", 2, 3, 2),
    "puppy": ("Stray puppy", "A tiny puppy wags at you hopefully.", 0, 2, 3),
    "flashsale": ("Ink & Steel flash sale", "\"50% off all piercings today only!\" says the sign.", 0, 2, 3),
    "preacher": ("Street preacher", "\"Repent, Genitopia! Abstinence is the only way!\" he shouts.", 0, 2, 2),
}


def active(gs: GameState, key: str) -> bool:
    return any(e.key == key for e in gs.events)


def remove(gs: GameState, ev: TownEvent) -> None:
    if ev in gs.events:
        gs.events.remove(ev)


def tick_events(gs: GameState) -> None:
    for ev in list(gs.events):
        ev.slots_left -= 1
        if ev.slots_left <= 0:
            gs.events.remove(ev)
    if gs.raining and gs.rng.random() < 0.5:
        gs.raining = False
        gs.say("The rain stops. Genitopia glistens.")


def maybe_spawn_event(gs: GameState) -> None:
    rng = gs.rng
    if not gs.raining and rng.random() < 0.08:
        gs.raining = True
        gs.say("Rain rolls over Genitopia. Everyone runs for cover.")
    if len(gs.events) >= 3 or rng.random() > 0.45:
        return
    options = [k for k, (_, _, lo, hi, _) in CATALOGUE.items()
               if lo <= gs.slot <= hi and not active(gs, k)]
    free = [s for s in EVENT_SPOTS if all((e.x, e.y) != s for e in gs.events)]
    if not options or not free:
        return
    key = rng.choice(options)
    title, _, _, _, dur = CATALOGUE[key]
    x, y = rng.choice(free)
    gs.events.append(TownEvent(key, title, x, y, dur))
    gs.say(f"Something's happening in town: {title.lower()}.")


def spawn(gs: GameState, key: str, x: int = 660, y: int = 700) -> TownEvent:
    """Force an event (used by tests)."""
    title, _, _, _, dur = CATALOGUE[key]
    ev = TownEvent(key, title, x, y, dur)
    gs.events.append(ev)
    return ev


def intro(ev: TownEvent) -> str:
    return CATALOGUE[ev.key][1]


def options(gs: GameState, ev: TownEvent) -> list[EventOption]:
    k = ev.key

    def done(fn):
        """Wrap an effect so the event disappears afterwards."""
        def run(g):
            err = fn(g)
            if not err:
                remove(g, ev)
            return err
        return run

    if k == "busker":
        def tip(g):
            if g.money < 5:
                return "You're broke. He plays a sad song for you anyway."
            g.money -= 5
            g.adjust(mood=10)
            g.say("You tip $5. He winks and plays your name into the solo.")
        def dance(g):
            g.adjust(mood=8, energy=-5)
            g.say("You dance on the sidewalk. A small crowd cheers.")
        return [EventOption("Tip $5", "+Mood", tip), EventOption("Dance along", "+Mood, -Energy", dance)]

    if k == "tacotruck":
        def tacos(g):
            if g.money < 6:
                return "Tacos are $6."
            g.money -= 6
            g.adjust(fullness=30, mood=6)
            msg = "Three tacos, extra salsa. Life is good."
            if g.craving == "spicy tacos":
                g.craving = None
                g.adjust(mood=20)
                msg += " Craving: SATISFIED."
            g.say(msg)
        return [EventOption("Buy tacos", "$6 · +30 fullness", tacos)]

    if k == "wallet":
        def keep(g):
            g.money += 40
            g.adjust(mood=-6)
            g.say("You pocket $40 and toss the wallet. You feel a bit gross about it.")
        def hand_in(g):
            g.money += 20
            g.adjust(mood=12)
            g.say("You hand it to Officer Woody. The owner sends you $20 as thanks!")
        return [EventOption("Turn it in", "Do the right thing", done(hand_in)),
                EventOption("Keep the cash", "+$40, guilty conscience", done(keep))]

    if k == "giveaway":
        def take(g):
            g.condoms += 2
            g.say("Nurse Ova hands you two condoms and a pamphlet. \"Get tested regularly, hun!\"")
        return [EventOption("Take free condoms", "+2 condoms", done(take))]

    if k == "blockparty":
        def party(g):
            if g.energy < 15:
                return "Too tired to party."
            g.adjust(mood=20, energy=-15, hygiene=-10)
            p = Partner.random(g.rng, None if g.show_me == "everyone" else g.show_me)
            msg = "You dance under the string lights until your feet hurt."
            if g.rng.random() < 0.3 + g.charm / 200:
                g.add_match(p)
                msg += f" {p.name} dances with you and asks for your number!"
            g.say(msg)
            g.advance()
        return [EventOption("Join the party", "+Mood, maybe meet someone", party)]

    if k == "puppy":
        def pet(g):
            g.adjust(mood=12)
            g.say("You pet the puppy. It licks your face. Best moment of the week.")
        return [EventOption("Pet the puppy", "+Mood", pet)]

    if k == "flashsale":
        return [EventOption("Noted!", "Piercings are half price while this lasts", lambda g: None)]

    if k == "preacher":
        def argue(g):
            g.adjust(mood=-4, energy=-4)
            g.say("You argue about safe sex vs abstinence. Nobody wins.")
        def pamphlet(g):
            g.adjust(mood=3)
            g.say("You take a pamphlet. It makes a decent coaster.")
        return [EventOption("Argue with him", "-Mood", argue), EventOption("Take a pamphlet", "", pamphlet)]

    return []
