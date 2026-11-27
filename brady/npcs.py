"""Residents of Genitopia: who they are, what they say (changes daily) and how to romance them."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from .model import Character, GameState, Partner

Effect = Callable[[GameState], None]
Cond = Callable[[GameState], bool]


@dataclass
class Reply:
    text: str
    response: str
    effect: Effect | None = None
    aff: int = 3                    # affection gained with this resident


@dataclass
class Line:
    text: str                       # may use {name} {weekday} {opp} {record} {last} {baby} {gossip_a} ...
    replies: list[Reply]
    cond: Cond | None = None        # topical lines: only said when true, once per day
    lid: str = ""                   # filled in automatically


@dataclass
class Npc:
    key: str
    name: str
    role: str
    look: Character
    room: str                       # "town" or a room key
    pos: tuple[int, int]
    age: int
    daily: list[Line] = field(default_factory=list)
    topical: list[Line] = field(default_factory=list)
    patrol: list[tuple[int, int]] = field(default_factory=list)
    decline: str = ""               # non-empty: politely not interested in romance
    sti_risk: float = 0.08


# ---- small helpers ---------------------------------------------------------------
def fx(**kw) -> Effect:
    return lambda g: g.adjust(**kw)


def money(n) -> Effect:
    def run(g):
        g.money += n
    return run


def pregnant(g):
    return g.conception is not None and g.conception.revealed


def has_baby(g):
    return g.baby is not None


def ctx(gs: GameState) -> dict:
    from .baseball import opponent, record
    from .jobs import JOBS
    rng = random.Random(gs.day * 7919)
    names = [n.name for n in NPCS]
    a, b = rng.sample(names, 2)
    return {
        "name": gs.character.name, "weekday": gs.weekday, "opp": opponent(gs), "record": record(gs),
        "last": gs.last_game or "haven't played yet", "baby": gs.baby.name if gs.baby else "the baby",
        "job": JOBS[gs.job].title.lower() if gs.job else "unemployed", "gossip_a": a, "gossip_b": b,
    }


def say(text: str, gs: GameState) -> str:
    try:
        return text.format(**ctx(gs))
    except (KeyError, IndexError):
        return text


# ---- lines every resident can bring up --------------------------------------------
from .baseball import is_game_day  # noqa: E402
from .cycle import phase  # noqa: E402

SHARED_TOPICAL = [
    Line("Big game tonight! The Ballers take on the {opp}. You coming to the stadium?", [
        Reply("Wouldn't miss it!", "\"Go Ballers! Wear your lucky jock.\"", fx(mood=4)),
        Reply("Baseball's boring", "\"Blasphemy. In Genitopia?!\"", aff=-2)],
        lambda g: is_game_day(g) and g.slot <= 2),
    Line("Did you hear? The Ballers {last}. Season record's {record}.", [
        Reply("What a game!", "\"Right?! I lost my voice.\"", fx(mood=3)),
        Reply("I missed it", "\"Next time, come watch. Or play!\"")],
        lambda g: bool(g.last_game) and g.day % 3 == 1),
    Line("Ugh, this rain. Genitopia gets so... moist.", [
        Reply("Ha! Gross.", "\"I stand by it.\"", fx(mood=3)),
        Reply("I like the rain", "\"You would.\"")], lambda g: g.raining),
    Line("You look stressed. Bills piling up?", [
        Reply("Rent is killing me", "\"Genitopia rent is criminal. Hang in there.\"", fx(mood=3), 5),
        Reply("I'm fine!", "\"Mm-hm. Sure.\"")], lambda g: any(b.overdue(g) for b in g.bills)),
    Line("Hey, you okay? You look like you need a heating pad and a hug.", [
        Reply("Period cramps...", "\"Oof. Painkillers and chocolate. Doctor's orders.\"", fx(mood=5), 6),
        Reply("I'm good, thanks", "\"Alright, tough cookie.\"")], lambda g: phase(g) == "period"),
    Line("Want some chocolate? No reason. You just look like a chocolate kind of day.", [
        Reply("YES. Gimme.", "They hand you a chocolate bar. Hero.", fx(mood=8, fullness=5), 6),
        Reply("Are you saying I'm cranky?", "\"...No?\" They back away slowly.", aff=-1)],
        lambda g: phase(g) == "pms"),
    Line("Whoa, aren't you the Ballers' big hitter? Can I get an autograph?", [
        Reply("Sure thing!", "You sign their arm. They swear they'll never wash it.", fx(mood=6), 5),
        Reply("No photos please", "\"A true celebrity.\"")], lambda g: g.fame >= 10),
    Line("I heard you got a hot tub. Fancy! Hosting parties now?", [
        Reply("Invite only ;)", "\"Ooh. Put me on the list.\"", aff=6),
        Reply("It's just for me", "\"Self-care queen. Respect.\"")], lambda g: "hottub" in g.upgrades),
    Line("Ugh, Monday. Coffee hasn't kicked in yet.", [
        Reply("Same", "\"Solidarity.\"", fx(mood=2)),
        Reply("I love Mondays", "\"Who hurt you?\"")], lambda g: g.weekday == "Monday"),
    Line("It's FRIDAY! Got any big plans tonight?", [
        Reply("Club Velvet, baby", "\"Save me a dance.\"", aff=5),
        Reply("Sleep", "\"Honestly? Iconic.\"")], lambda g: g.weekday == "Friday"),
    Line("Lazy Sunday, huh? I haven't changed out of my sweatpants.", [
        Reply("Same, no shame", "\"Sweatpants gang.\"", fx(mood=3)),
        Reply("I'm being productive", "\"Ew.\"")], lambda g: g.weekday == "Sunday"),
    Line("Still looking for work? The stadium and the diner are always hiring.", [
        Reply("Thanks for the tip", "\"Anytime.\"", aff=3),
        Reply("I'm on a break", "\"A long one, it seems.\"")], lambda g: g.job is None),
    Line("How's little {baby} doing? Sleeping through the night yet?", [
        Reply("Ha, no", "\"Coffee. Lots of coffee.\"", fx(mood=3)),
        Reply("They're perfect", "\"Aww. Proud parent!\"", fx(mood=4))], has_baby),
    Line("Not to be rude, but... when did you last shower?", [
        Reply("Rude!", "\"I said not to be rude!\"", fx(mood=-3), -2),
        Reply("...Fair point", "\"Go on. I'll wait.\"")], lambda g: g.hygiene < 30),
    Line("Block party tonight! I heard the DJ is amazing.", [
        Reply("See you there", "\"It's a date. Kinda.\"", aff=5),
        Reply("Not my scene", "\"Party pooper.\"")], lambda g: any(e.key == "blockparty" for e in g.events)),
]

GOSSIP = [
    "Did you hear? {gossip_a} was seen sharing a milkshake with {gossip_b} at Bean's. Two straws!",
    "Rumor is {gossip_a} has a secret piercing. Don't ask where.",
    "{gossip_a} lost a bet on the Ballers and had to wear a chicken costume all day.",
    "Somebody saw {gossip_a} and {gossip_b} skinny dipping in the fountain at 2am!",
    "{gossip_a} swears the hot dogs at the stadium are 'life-changing'. Seems like a cry for help.",
    "Word is {gossip_a} has a crush on someone in town. They won't say who!",
]


def gossip_line(gs) -> Line:
    text = GOSSIP[gs.day % len(GOSSIP)]
    return Line(text, [Reply("No way!", "\"Way. You didn't hear it from me.\"", fx(mood=3), 4),
                       Reply("Spill the tea", "They lean in and whisper for ten minutes. Juicy.", fx(mood=5), 5)],
                lid="gossip")


# ---- the residents ------------------------------------------------------------------
def L(text, *replies, cond=None):
    return Line(text, [Reply(*r) if isinstance(r, tuple) else r for r in replies], cond)


NPCS = [
    Npc("mayor", "Mayor Johnson", "Mayor of Genitopia", Character("penis", "Mayor Johnson", "Beige", "Gray", "tophat"),
        "town", (1420, 940), 58, daily=[
            L("Welcome to Genitopia, where everyone's a little... exposed! Ha! Enjoying our fair town?",
              ("Love it here!", "\"Wonderful! Vote Johnson!\" He hands you a sticker."),
              ("The potholes, though...", "\"Ah. Yes. We're... looking into it.\" He sweats.")),
            L("The Block Party committee wants a bigger budget. What do you think?",
              ("More parties!", "\"A person of the people! I like it.\""),
              ("Fix the roads first", "\"Sensible. Boring, but sensible.\"")),
            L("I'm thinking of building a statue in Genitopia Square. Of me. Thoughts?",
              ("Make it life-size", "\"Bigger. Much bigger.\""),
              ("That's vain", "\"It's called LEGACY.\"", None, -1)),
            L("It's {weekday} and I've already cut four ribbons. Being mayor is exhausting.",
              ("You work hard", "\"Finally, someone notices!\"", None, 5),
              ("Cutting ribbons?", "\"Ceremonial scissors are heavy!\"")),
            L("Between you and me, I've never actually caught a baseball. Don't tell the voters.",
              ("Your secret's safe", "\"I knew I liked you.\"", None, 6),
              ("I'm telling everyone", "\"You wouldn't DARE.\"")),
            L("Genitopia's tourism slogan: 'Come for the fountain, stay for the... everything.' Good?",
              ("Perfect", "\"I'll put it on a mug.\""),
              ("Needs work", "\"Everyone's a critic.\"")),
        ], topical=[
            L("Congratulations on the little one! Genitopia's population grows!",
              ("Thanks, Mayor!", "\"A gift from the town!\" He gives you $25.", money(25)), cond=has_baby),
        ], sti_risk=0.12),
    Npc("granny", "Granny Muffin", "Lifelong resident", Character("vagina", "Granny Muffin", "Pink", "Gray", "glasses"),
        "town", (640, 940), 79, decline="\"Oh honey, I'm flattered. But my heart belongs to Wheel of Fortune.\"", daily=[
            L("Back in my day we used condoms made of sheep guts, dearie. You kids have it easy.",
              ("Ew, Granny!", "\"Ha! Wrap it up, that's all I'm saying.\"", fx(mood=3)),
              ("Got any candy?", "She hands you a butterscotch.", fx(fullness=5, mood=4))),
            L("I've seen that look before. Somebody special on your mind?",
              ("Maybe...", "\"Treat them right. And get tested together, it's romantic!\"", fx(mood=6)),
              ("Single and loving it", "\"Good for you! Live a little!\"", fx(mood=4))),
            L("I knitted a cozy for the fountain. The Mayor says it's 'not regulation'.",
              ("It's beautiful", "\"Thank you, dear. He's just jealous.\"", None, 5),
              ("A fountain cozy?", "\"Fountains get cold too!\"")),
            L("My late husband played for the Ballers in '62. Struck out every time. Lovely man.",
              ("Aww", "\"He had other talents.\" She winks. Oh no.", fx(mood=4)),
              ("Every time?", "\"Every. Single. Time.\"")),
            L("It's {weekday}! I've got bingo at four and a hot date with my crossword after.",
              ("Living the dream", "\"Don't you know it.\""),
              ("Can I come to bingo?", "\"Only if you bring snacks.\"", None, 5)),
            L("You young people and your swiping. In my day we just winked across the dance hall.",
              ("Teach me to wink", "She winks. It's devastating.", fx(mood=5)),
              ("Swiping is easier", "\"Easier isn't better, sweetie.\"")),
        ], topical=[
            L("Oh my, look at that bump! Put your feet up, sweetheart.",
              ("I'm craving weird stuff", "\"With my first I ate pickles with jam!\"", fx(mood=6)),
              ("I'm scared", "She squeezes your hand. \"You'll be wonderful.\"", fx(mood=10)),
              cond=lambda g: g.is_carrier and pregnant(g)),
            L("Is that the baby? Let me see! Oh, coochie-coo!",
              ("Want to hold them?", "She rocks the baby and hums.", lambda g: setattr(g.baby, "happiness", 100)),
              cond=lambda g: g.baby_with_you),
        ]),
    Npc("officer", "Officer Woody", "Genitopia PD", Character("penis", "Officer Woody", "Brown", "Black", "cap"),
        "town", (1300, 600), 34, patrol=[(1300, 600), (1300, 1500), (1300, 950), (2500, 950), (1300, 950), (100, 950)],
        daily=[
            L("Evening. Keep it legal and keep it consensual, citizen.",
              ("Yes, officer", "\"Good. Carry on.\""),
              ("Nice hat", "\"...Thank you. It's regulation.\" He blushes.", None, 6)),
            L("Somebody turned in a wallet the other day. Honest folks make my job easy.",
              ("I'd turn one in too", "\"That's what I like to hear.\"", fx(mood=3))),
            L("Quiet shift so far. Last week someone streaked through the stadium. Twice.",
              ("Did you catch them?", "\"Second time, yes. First time I was... impressed.\""),
              ("Sounds fun", "\"Don't get any ideas.\"")),
            L("I've been patrolling all {weekday}. My feet are killing me.",
              ("Want a foot rub?", "\"Is that... a legal offer?\" He's blushing again.", None, 7),
              ("Sit down a sec", "\"Can't. Crime never sleeps.\"")),
            L("Fun fact: Genitopia has the lowest crime rate in the county. Highest condom sales too.",
              ("Correlation?", "\"I'm a cop, not a scientist.\""),
              ("Proud of us", "\"Me too, citizen.\"")),
            L("You know, I joined the force for the uniform. Stayed for the people.",
              ("The uniform works", "\"...You think so?\"", None, 7),
              ("That's sweet", "\"Don't tell anyone.\"")),
        ], sti_risk=0.05),
    Npc("jaz", "Jaz", "Jogs every day", Character("vagina", "Jaz", "Brown", "Red", "headband"),
        "town", (1560, 1500), 26, patrol=[(1520, 1440), (1800, 1440), (1800, 1590), (1520, 1590)], daily=[
            L("Five miles down! Want to join me tomorrow? Six AM!",
              ("Six AM?!", "\"The sunrise is worth it. Mostly.\""),
              ("Count me in", "\"I'll hold you to that!\"", None, 6)),
            L("I'm training for the Genitopia Marathon. It's 26 miles of pure suffering.",
              ("Why do it?", "\"The medal. And the post-race nachos.\""),
              ("You're amazing", "\"Stop, I'm sweating AND blushing now.\"", None, 7)),
            L("Saw a squirrel steal an entire hot dog outside the stadium. Respect.",
              ("Legend", "\"An icon. A role model.\"", fx(mood=3))),
            L("Happy {weekday}! Fun fact: running releases endorphins. So does kissing. Just saying.",
              ("Is that an invitation?", "\"Maybe. Keep up and find out.\"", None, 8),
              ("I'll stick to running", "\"Your loss!\"")),
            L("I have three playlists: Run, Cry, and Run While Crying.",
              ("Which one today?", "\"Run. Thank you for asking.\""),
              ("Same", "\"Kindred spirits.\"", None, 5)),
        ], sti_risk=0.07),
    Npc("chef", "Chef Bean", "Owns the Diner", Character("penis", "Chef Bean", "Tan", "Brown", "chefhat"),
        "diner", (450, 184), 41, daily=[
            L("Order up! You look hungry, friend.",
              ("Starving", "\"Then sit down, I've got you.\""),
              ("What's good today?", "\"Everything. But the milkshake? Life-changing.\"")),
            L("Today's special is the {weekday} Meatball Surprise. The surprise is extra meatballs.",
              ("Love a surprise", "\"I knew you would.\""),
              ("Pass", "\"Your loss.\"")),
            L("I've been perfecting a new sauce. Secret ingredient is love. And paprika. Mostly paprika.",
              ("Can I taste?", "He feeds you a spoonful. Wow.", fx(mood=5, fullness=3), 6),
              ("Keep your secrets", "\"Oh, I will.\"")),
            L("A food critic from Scrotum City is coming next week. I haven't slept.",
              ("You'll crush it", "\"From your lips to God's ears.\"", None, 5),
              ("Scrotum City food sucks", "\"RIGHT?! Thank you!\"", None, 6)),
            L("You know what goes great with fries? Someone to share them with.",
              ("Are you flirting?", "\"With a spatula in my hand? Always.\"", None, 7),
              ("Ketchup?", "\"...Yes. Also ketchup.\"")),
        ], topical=[
            L("Cravings again? I keep pickles AND ice cream in stock for expectant folks.",
              ("You're a hero", "\"I know.\"", fx(mood=5)), cond=lambda g: g.craving is not None),
        ], sti_risk=0.08),
    Npc("patty", "Pharmacist Patty", "Pharmacy", Character("vagina", "Patty", "Brown", "Red", "glasses"),
        "pharmacy", (400, 164), 29, daily=[
            L("Condoms are aisle 3, pregnancy tests aisle 4, and judgement is not sold here.",
              ("Ha, thanks", "\"Anytime. Stay safe out there.\""),
              ("Any advice?", "\"Condoms protect from STIs AND pregnancy. Pulling out? Not so much.\"")),
            L("Fun fact: we sell more condoms on Ballers game nights than any other night.",
              ("Home runs, huh?", "\"I see what you did there.\"", fx(mood=3), 5),
              ("Good to know", "\"Stock up!\"")),
            L("It's {weekday}, I've filled 40 prescriptions and someone asked me if lube expires. It does.",
              ("Wait, it does?", "\"Check the bottle! Science!\""),
              ("Poor you", "\"Thank you. Truly.\"", None, 5)),
            L("Reminder: STI tests at Genitopia General are quick, cheap and nothing to be shy about.",
              ("Good reminder", "\"I'm basically a public service.\""),
              ("You sound like a poster", "\"I AM the poster. Check the clinic wall.\"")),
            L("Between you and me, I've had a crush on someone in town for months.",
              ("Who?!", "\"...Not telling. Yet.\" She looks right at you.", None, 7),
              ("Go for it", "\"Maybe I will.\"")),
        ], topical=[
            L("Little one needs formula? I'll throw in a free bib.",
              ("Thank you!", "\"Babies are messy. Trust me.\"", fx(mood=4)), cond=has_baby),
            L("Period supplies are aisle 2, painkillers right by the register. Heating pads too.",
              ("Lifesaver", "\"That's literally my job.\"", fx(mood=3)), cond=lambda g: phase(g) in ("period", "pms")),
        ], sti_risk=0.03),
    Npc("ova", "Dr. Ova", "Genitopia General", Character("vagina", "Dr. Ova", "Ebony", "Black", "glasses"),
        "clinic", (440, 184), 45, decline="\"I'm flattered, but I don't date patients. Ethics, darling.\"", daily=[
            L("Regular testing is self-care! Anything bothering you today?",
              ("All good, doc", "\"Love to hear it.\""),
              ("Just here to chat", "\"My favorite kind of patient.\"")),
            L("Doctor's tip of the day: hydrate. Then hydrate again.",
              ("Yes, doctor", "\"Good patient.\""),
              ("Does coffee count?", "\"...Technically.\"")),
            L("We had three Ballers in here after last game. Sliding into second is NOT for amateurs.",
              ("Ouch", "\"Ouch indeed.\""),
              ("I'd never", "\"Famous last words.\"")),
            L("Happy {weekday}. Remember: if something itches, burns or looks weird, come see me. No shame.",
              ("Noted", "\"Good.\""),
              ("Everything looks weird", "\"Then come in more often!\"")),
        ], topical=[
            L("I can see from here something's not right. Let me take a look, no shame.",
              ("Okay...", "\"Use the exam option and we'll sort you out.\""), cond=lambda g: g.infection is not None),
            L("How's the pregnancy going? Rest, eat, and come in when labor starts.",
              ("Tired all the time", "\"Totally normal. Naps are medicine.\"", fx(mood=5, energy=5)),
              ("Excited!", "\"That's the spirit!\"", fx(mood=6)), cond=pregnant),
        ]),
    Npc("rocco", "Rocco", "Bartender at Club Velvet", Character("penis", "Rocco", "Ebony", "Black", ""),
        "club", (200, 164), 31, daily=[
            L("What'll it be, gorgeous?",
              ("Surprise me", "He slides you something pink and glowing. \"On the house.\"", fx(mood=8, health=-1)),
              ("Just water", "\"Hydration is sexy.\"")),
            L("See that one on the dance floor? They've been looking at you all night.",
              ("Really?!", "\"Go say hi. Worst case, they say no.\"", fx(mood=6)),
              ("I'm looking at you", "He grins. \"Careful. I make strong drinks.\"", None, 8)),
            L("New cocktail: the Genitopia Sunset. Tequila, grenadine, bad decisions.",
              ("One please", "\"Coming right up.\"", fx(mood=6, health=-1)),
              ("Sounds dangerous", "\"That's the point.\"")),
            L("{weekday} crowd's wild tonight. Someone already proposed on the dance floor.",
              ("Did they say yes?", "\"They said 'maybe after this song'.\""),
              ("Romantic", "\"You a romantic?\"", None, 5)),
            L("I've seen it all from behind this bar. First kisses, breakups, a goat once.",
              ("A GOAT?", "\"Don't ask. He tipped well.\""),
              ("Tell me everything", "He leans in. Stories for hours.", None, 6)),
        ], sti_risk=0.2),
    Npc("pierce", "Pierce", "Piercer at Ink & Steel", Character("penis", "Pierce", "Beige", "Black", "studs"),
        "studio", (300, 300), 27, daily=[
            L("Pain is temporary. Bling is forever. What are we poking today?",
              ("Does it hurt?", "\"Like a mosquito with a grudge. You'll live.\""),
              ("Just browsing", "\"Browse away. Clean hands only.\"")),
            L("I pierced the Mayor last week. Can't say where. Professional secrecy.",
              ("Tell me!", "\"My lips are sealed. And pierced.\""),
              ("I don't want to know", "\"Wise.\"")),
            L("New titanium shipment just came in. Hypoallergenic AND shiny.",
              ("Ooh shiny", "\"Right?! I knew you had taste.\"", None, 5),
              ("Cool cool", "\"Cool cool cool.\"")),
            L("It's {weekday}. I've done six ears, two tongues and one... we don't talk about it.",
              ("Now I need to know", "\"Let's just say: very brave.\""),
              ("Busy day", "\"Living the dream.\"")),
        ], topical=[
            L("Keep that new piercing clean, yeah? Saline rinse, no picking.",
              ("Got it", "\"Good human.\""), cond=lambda g: g.piercing_heal > 0),
        ], sti_risk=0.18),
    Npc("boss", "Boss Richard", "Office manager", Character("penis", "Richard", "Pink", "Brown", "glasses"),
        "office", (120, 144), 50, decline="\"HR has a whole binder about this. A BINDER.\"", daily=[
            L("Those TPS reports won't file themselves.",
              ("On it, boss", "\"That's what I like to hear.\""),
              ("Can I get a raise?", "\"Ha! ...Work more shifts.\"", None, -1)),
            L("Mandatory fun this {weekday}: trust falls in the break room.",
              ("Sounds fun", "\"It's MANDATORY fun.\""),
              ("I'll be sick that day", "\"I'll need a doctor's note.\"")),
            L("Someone microwaved fish again. If I find out who...",
              ("Wasn't me", "\"That's what the guilty say.\""),
              ("It was Rocco", "\"Rocco doesn't even work here!\"")),
        ], topical=[
            L("I heard about the baby! Take it easy this week. Here's a little bonus.",
              ("Thanks, Richard!", "\"Don't get used to it.\" +$30", money(30)),
              cond=lambda g: g.baby is not None and "boss:bonus" not in g.talked_today and not g.affection.get("boss_bonus")),
        ]),
    Npc("coach", "Coach Rod", "Ballers head coach", Character("penis", "Coach Rod", "Brown", "Black", "redcap"),
        "ballpark", (420, 420), 38, daily=[
            L("Ballers are {record} this season. We need a big bat. You ever swing one?",
              ("All the time", "\"Ha! Get in the batting cage and prove it.\"", None, 5),
              ("Never", "\"Everyone starts somewhere. Batting cage, $5.\"")),
            L("Next opponent: the {opp}. They play dirty. Real dirty.",
              ("We'll crush 'em", "\"THAT's the spirit!\"", fx(mood=5)),
              ("How dirty?", "\"They rub mud on EVERYTHING.\"")),
            L("Keep your eye on the ball, hips loose, and swing through. Like life.",
              ("Deep, coach", "\"I've been told.\""),
              ("Hips loose?", "\"Loose. Like this.\" He demonstrates. Wow.", None, 6)),
            L("Happy {weekday}. I've watched 300 hours of game tape this week. I need a hobby.",
              ("I could be your hobby", "He drops his clipboard. \"...Come again?\"", None, 8),
              ("Baseball IS a hobby", "\"Not the way I do it.\"")),
        ], topical=[
            L("It's game night! Grab a bat and get to home plate, slugger!",
              ("Put me in, coach!", "\"That's what I like to hear!\"", fx(mood=5)), cond=lambda g: is_game_day(g) and g.slot == 2),
        ], sti_risk=0.1),
    Npc("mandy", "Mandy", "Owns Screw & Nail", Character("vagina", "Mandy", "Tan", "Brown", "hardhat"),
        "hardware", (400, 168), 36, daily=[
            L("Welcome to Screw & Nail! If we don't have it, you don't need it.",
              ("Love the name", "\"Thank you! Took me ages.\" (It did not.)"),
              ("Got any duct tape?", "\"Aisle 1, 2 AND 3.\"")),
            L("I can install a hot tub in an afternoon. Just saying. Just putting that out there.",
              ("Tempting", "\"It's always tempting.\""),
              ("Join me in it?", "\"...I'd have to check it's installed right.\" She winks.", None, 8)),
            L("Happy {weekday}! Fixed three toilets, a fence and the Mayor's ego. Busy day.",
              ("The ego was hardest?", "\"Industrial strength glue.\""),
              ("You fix everything", "\"Except my love life.\"", None, 6)),
            L("You know what makes a house a home? A really good set of power tools.",
              ("And love?", "\"Love AND power tools.\""),
              ("Show me your drill", "\"Smooth.\" She laughs.", None, 6)),
        ], sti_risk=0.06),
]
NPC_BY_KEY = {n.key: n for n in NPCS}
for _n in NPCS:
    for _i, _ln in enumerate(_n.daily):
        _ln.lid = f"{_n.key}:d{_i}"
    for _i, _ln in enumerate(_n.topical):
        _ln.lid = f"{_n.key}:t{_i}"
for _i, _ln in enumerate(SHARED_TOPICAL):
    _ln.lid = f"shared:{_i}"


# ---- choosing what to say ----------------------------------------------------------
def pick_line(gs: GameState, npc: Npc) -> Line:
    """Topical lines first (each once a day), then today's gossip, then the daily rotation."""
    said = gs.talked_today
    for ln in npc.topical:
        if ln.cond and ln.cond(gs) and ln.lid not in said:
            return ln
    for ln in SHARED_TOPICAL:
        if ln.cond(gs) and f"{npc.key}/{ln.lid}" not in said:
            return Line(ln.text, ln.replies, ln.cond, f"{npc.key}/{ln.lid}")
    if f"{npc.key}/gossip" not in said and (gs.day + len(npc.key)) % 2 == 0:
        g = gossip_line(gs)
        g.lid = f"{npc.key}/gossip"
        return g
    order = list(range(len(npc.daily)))
    random.Random(gs.day * 131 + sum(map(ord, npc.key))).shuffle(order)
    today = sum(1 for x in said if x.startswith(npc.key + ":d"))
    return npc.daily[order[today % len(order)]]


def respond(gs: GameState, npc: Npc, line: Line, reply: Reply) -> None:
    gs.talks[npc.key] = gs.talks.get(npc.key, 0) + 1
    gs.talked_today.add(line.lid)
    if npc.key == "boss" and line.cond:
        gs.affection["boss_bonus"] = 1
    change_affection(gs, npc, reply.aff)
    gs.say(f"You: \"{reply.text}\"  {npc.name}: {say(reply.response, gs)}")
    if reply.effect:
        reply.effect(gs)


def npcs_in(room: str, gs: GameState | None = None) -> list[Npc]:
    out = [n for n in NPCS if n.room == room]
    if gs is not None and gs.date is not None and gs.date_place == "home":
        out = [n for n in out if n.name != gs.date.name]     # they're at your place
    return out


# ---- romance --------------------------------------------------------------------------
def affection(gs, npc: Npc) -> int:
    return gs.affection.get(npc.key, 0)


def change_affection(gs, npc: Npc, amount: int) -> None:
    if npc.decline:
        amount = min(amount, 3)
    gs.affection[npc.key] = max(0, min(100, affection(gs, npc) + amount))


def stage(gs, npc: Npc) -> str:
    a = affection(gs, npc)
    if npc.decline:
        return "Friendly"
    return "Stranger" if a < 15 else "Friend" if a < 35 else "Crush" if a < 65 else "Dating"


def as_partner(gs, npc: Npc) -> Partner:
    return Partner(npc.name, npc.age, npc.look.kind, npc.role, "", 0.6 + affection(gs, npc) / 250,
                   npc.sti_risk, npc.look.body_color, npc.look.hair_color)


def npc_for(name: str) -> Npc | None:
    return next((n for n in NPCS if n.name == name), None)


FLIRT_OK = ["{n} blushes and bites their lip. \"Keep talking.\"",
            "{n} laughs and touches your arm. \"You're trouble.\"",
            "{n} leans in closer. \"Is that a line? Because it's working.\""]
FLIRT_BAD = ["{n} raises an eyebrow. \"...Okay then.\"",
             "{n} pats your shoulder. \"Nice try, champ.\""]
DATES = [("dinner at Bean's", "You split a milkshake. Two straws. Very cute."),
         ("a walk around Genitopia Square", "You toss coins in the fountain and hold hands."),
         ("the batting cages", "They wrap their arms around you to 'fix your swing'. Sure."),
         ("Club Velvet", "You slow-dance to a fast song. Nobody cares.")]


def flirt(gs, npc: Npc) -> str | None:
    tag = f"flirt:{npc.key}"
    if tag in gs.talked_today:
        return f"Don't overdo it. Try {npc.name.split()[-1]} again tomorrow."
    gs.talked_today.add(tag)
    if npc.decline:
        gs.say(f"{npc.name}: {npc.decline}")
        return None
    chance = 0.3 + gs.charm / 140 + affection(gs, npc) / 200
    if gs.rng.random() < chance:
        change_affection(gs, npc, 10)
        gs.adjust(mood=6)
        gs.say(gs.rng.choice(FLIRT_OK).format(n=npc.name) + f" ({stage(gs, npc)})")
    else:
        change_affection(gs, npc, -3)
        gs.adjust(mood=-4)
        gs.say(gs.rng.choice(FLIRT_BAD).format(n=npc.name))
    return None


def go_on_date(gs, npc: Npc) -> str | None:
    if npc.decline:
        return None
    if affection(gs, npc) < 35:
        return f"{npc.name} isn't into you like that (yet). Flirt more!"
    tag = f"date:{npc.key}"
    if tag in gs.talked_today:
        return "You already went out today."
    if gs.money < 25:
        return "A date costs about $25."
    gs.talked_today.add(tag)
    gs.money -= 25
    where, what = gs.rng.choice(DATES)
    change_affection(gs, npc, 15)
    gs.adjust(mood=14, fullness=10)
    gs.say(f"You take {npc.name} to {where}. {what} ({stage(gs, npc)})")
    gs.advance()
    return None


def invite_home(gs, npc: Npc) -> str | None:
    if npc.decline:
        return None
    if affection(gs, npc) < 65:
        return f"{npc.name} wants to take things slower. Go on more dates."
    if not gs.is_night_time:
        return "\"Tonight, maybe? Ask me this evening.\""
    gs.date = as_partner(gs, npc)
    gs.date_place = "home"
    tub = " And bring your swimsuit... or don't." if "hottub" in gs.upgrades else ""
    gs.say(f"{npc.name}: \"Your place? I'll meet you there.\"{tub} (Head home to your bedroom.)")
    if "hottub" in gs.upgrades:
        change_affection(gs, npc, 5)
    return None


def after_hookup(gs, p: Partner) -> None:
    npc = npc_for(p.name)
    if npc:
        change_affection(gs, npc, 10)
