"""Named residents of Genitopia and what they say to you."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .model import Character, GameState

Effect = Callable[[GameState], None]


@dataclass
class Reply:
    text: str
    response: str
    effect: Effect | None = None


@dataclass
class Line:
    text: str
    replies: list[Reply]
    cond: Callable[[GameState], bool] | None = None   # special lines win when true


@dataclass
class Npc:
    key: str
    name: str
    role: str
    look: Character
    room: str                      # "town" or a room key
    pos: tuple[int, int]
    lines: list[Line] = field(default_factory=list)
    patrol: list[tuple[int, int]] = field(default_factory=list)


def mood(n):
    return lambda g: g.adjust(mood=n)


def fx(**kw):
    return lambda g: g.adjust(**kw)


def money(n):
    def run(g):
        g.money += n
    return run


def pregnant(g):
    return g.conception is not None and g.conception.revealed


def smelly(g):
    return g.hygiene < 30


def has_baby(g):
    return g.baby is not None and not g.baby.in_crib


NPCS = [
    Npc("mayor", "Mayor Johnson", "Mayor of Genitopia",
        Character("penis", "Mayor Johnson", "Beige", "Gray", "tophat"), "town", (1420, 940), [
            Line("Welcome to Genitopia, where everyone's a little... exposed! Ha! Enjoying our fair town?", [
                Reply("Love it here!", "\"Wonderful! Vote Johnson!\" He hands you a sticker.", mood(5)),
                Reply("The potholes, though...", "\"Ah. Yes. We're... looking into it.\" He sweats a little."),
            ]),
            Line("The Block Party committee wants a bigger budget. What do you think?", [
                Reply("More parties!", "\"A person of the people! I like it.\"", mood(4)),
                Reply("Fix the roads first", "\"Sensible. Boring, but sensible.\""),
            ]),
            Line("Congratulations on the little one! Genitopia's population grows!", [
                Reply("Thanks, Mayor!", "\"Here, a gift from the town.\" He gives you $25.", money(25)),
            ], has_baby),
        ]),
    Npc("granny", "Granny Muffin", "Lifelong resident",
        Character("vagina", "Granny Muffin", "Pink", "Gray", "glasses"), "town", (640, 940), [
            Line("Back in my day we used condoms made of sheep guts, dearie. You kids have it easy.", [
                Reply("Ew, Granny!", "\"Ha! Wrap it up, that's all I'm saying.\"", mood(3)),
                Reply("Got any candy?", "She hands you a butterscotch. \"Don't tell your dentist.\"", fx(fullness=5, mood=4)),
            ]),
            Line("I've seen that look before. Somebody special on your mind?", [
                Reply("Maybe...", "\"Treat them right. And get tested together, it's romantic!\"", mood(6)),
                Reply("Nope, single and loving it", "\"Good for you! Live a little!\"", mood(4)),
            ]),
            Line("Oh my, look at that bump! Put your feet up, sweetheart.", [
                Reply("I'm craving weird stuff", "\"With my first I ate pickles with jam! Trust your belly.\"", mood(6)),
                Reply("I'm scared", "She squeezes your hand. \"You'll be wonderful.\"", mood(10)),
            ], lambda g: g.is_carrier and pregnant(g)),
            Line("Is that the baby? Let me see! Oh, coochie-coo!", [
                Reply("Want to hold them?", "She rocks the baby and hums. The baby is delighted.",
                      lambda g: setattr(g.baby, "happiness", 100)),
            ], has_baby),
        ]),
    Npc("officer", "Officer Woody", "Genitopia PD",
        Character("penis", "Officer Woody", "Brown", "Black", "cap"), "town", (1300, 600), [
            Line("Evening. Keep it legal and keep it consensual, citizen.", [
                Reply("Yes, officer", "\"Good. Carry on.\"", mood(2)),
                Reply("Nice hat", "\"...Thank you. It's regulation.\" He blushes.", mood(4)),
            ]),
            Line("Ma'am, sir, whatever you are: you smell like a crime scene. Go shower.", [
                Reply("Rude!", "\"I call it like I smell it.\"", mood(-3)),
                Reply("Fair point", "\"Appreciate the honesty.\""),
            ], smelly),
            Line("Somebody turned in a wallet the other day. Honest folks make my job easy.", [
                Reply("I'd turn one in too", "\"That's what I like to hear.\"", mood(3)),
            ]),
        ], patrol=[(1300, 600), (1300, 1500), (1300, 950), (2500, 950), (1300, 950), (100, 950)]),
    Npc("chef", "Chef Bean", "Owns the Diner",
        Character("penis", "Chef Bean", "Tan", "Brown", "chefhat"), "diner", (450, 105), [
            Line("Order up! You look hungry, friend.", [
                Reply("Starving", "\"Then sit down, I've got you.\""),
                Reply("What's good today?", "\"Everything. But the milkshake? Life-changing.\"", mood(3)),
            ]),
            Line("Cravings again? I keep pickles AND ice cream in stock just for expectant folks.", [
                Reply("You're a hero", "\"I know.\"", mood(5)),
            ], lambda g: g.craving is not None),
        ]),
    Npc("patty", "Pharmacist Patty", "Pharmacy",
        Character("vagina", "Patty", "Brown", "Red", "glasses"), "pharmacy", (450, 205), [
            Line("Condoms are aisle 3, pregnancy tests are aisle 4, and judgement is not sold here.", [
                Reply("Ha, thanks", "\"Anytime. Stay safe out there.\""),
                Reply("Any advice?", "\"Condoms protect from STIs AND pregnancy. Pulling out? Not so much.\"", mood(2)),
            ]),
            Line("Little one needs formula? I'll throw in a free bib.", [
                Reply("Thank you!", "\"Babies are messy. Trust me.\"", mood(4)),
            ], has_baby),
        ]),
    Npc("ova", "Dr. Ova", "Genitopia General",
        Character("vagina", "Dr. Ova", "Ebony", "Black", "glasses"), "clinic", (400, 185), [
            Line("Regular testing is self-care! Anything bothering you today?", [
                Reply("All good, doc", "\"Love to hear it. See you next time.\""),
                Reply("Just here to chat", "\"My favorite kind of patient.\"", mood(3)),
            ]),
            Line("I can see from here something's not right. Let me take a look, no shame.", [
                Reply("Okay...", "\"Use the exam option and we'll get you sorted.\""),
            ], lambda g: g.infection is not None),
            Line("How's the pregnancy going? Remember: rest, eat, and come in when labor starts.", [
                Reply("Tired all the time", "\"Totally normal. Naps are medicine.\"", fx(mood=5, energy=5)),
                Reply("Excited!", "\"That's the spirit!\"", mood(6)),
            ], pregnant),
        ]),
    Npc("rocco", "Rocco", "Bartender at Club Velvet",
        Character("penis", "Rocco", "Ebony", "Black", ""), "club", (400, 205), [
            Line("What'll it be, gorgeous?", [
                Reply("Surprise me", "He slides you something pink and glowing. \"On the house.\"", fx(mood=8, health=-1)),
                Reply("Just water", "\"Hydration is sexy.\"", mood(2)),
            ]),
            Line("See that one on the dance floor? They've been looking at you all night.", [
                Reply("Really?!", "\"Go say hi. Worst case, they say no.\"", mood(6)),
                Reply("Not tonight", "\"Suit yourself.\""),
            ]),
        ]),
    Npc("pierce", "Pierce", "Piercer at Ink & Steel",
        Character("penis", "Pierce", "Beige", "Black", "studs"), "studio", (200, 190), [
            Line("Pain is temporary. Bling is forever. What are we poking today?", [
                Reply("Does it hurt?", "\"Like a mosquito with a grudge. You'll live.\""),
                Reply("Just browsing", "\"Browse away. Clean hands only.\""),
            ]),
            Line("Keep that new piercing clean, yeah? Saline rinse, no picking.", [
                Reply("Got it", "\"Good human.\"", mood(2)),
            ], lambda g: g.piercing_heal > 0),
        ]),
    Npc("boss", "Boss Richard", "Your manager",
        Character("penis", "Richard", "Pink", "Brown", "glasses"), "office", (300, 300), [
            Line("Those TPS reports won't file themselves. Are you here to work?", [
                Reply("Absolutely, boss", "\"That's what I like to hear.\"", mood(-1)),
                Reply("Can I get a raise?", "\"Ha! ...No.\"", mood(-3)),
            ]),
            Line("I heard about the baby! Take it easy this week. Here's a little bonus.", [
                Reply("Thanks, Richard!", "\"Don't get used to it.\" +$30", money(30)),
            ], lambda g: g.baby is not None and g.talks.get("boss_bonus") is None),
        ]),
]
NPC_BY_KEY = {n.key: n for n in NPCS}

# Shop staff stand behind their counters (feet positions inside each room).
for _k, _pos in {"chef": (450, 184), "patty": (400, 164), "ova": (440, 184), "rocco": (200, 164),
                 "pierce": (300, 300), "boss": (120, 144)}.items():
    NPC_BY_KEY[_k].pos = _pos


def pick_line(gs: GameState, npc: Npc) -> Line:
    special = [ln for ln in npc.lines if ln.cond and ln.cond(gs)]
    if special:
        return special[0]
    generic = [ln for ln in npc.lines if not ln.cond]
    return generic[gs.talks.get(npc.key, 0) % len(generic)]


def respond(gs: GameState, npc: Npc, line: Line, reply: Reply) -> None:
    gs.talks[npc.key] = gs.talks.get(npc.key, 0) + 1
    if npc.key == "boss" and line.cond:
        gs.talks["boss_bonus"] = 1
    gs.say(f"You: \"{reply.text}\"  {npc.name}: {reply.response}")
    if reply.effect:
        reply.effect(gs)


def npcs_in(room: str) -> list[Npc]:
    return [n for n in NPCS if n.room == room]
