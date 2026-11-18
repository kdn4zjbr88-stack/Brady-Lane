"""Core game state for Brady (set in the town of Genitopia). No pygame imports: logic stays testable."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

TOWN_NAME = "Genitopia"
TIME_SLOTS = ["Morning", "Afternoon", "Evening", "Night"]
GAME_LENGTH_DAYS = 30
PREGNANCY_SHOWS_AFTER = 4     # days until symptoms show up
LABOR_AFTER = 12              # days from conception to labor (game time is compressed)
SWIPES_PER_DAY = 12

CHARACTER_TYPES = ("penis", "vagina")

BODY_COLORS = {
    "Ebony": (74, 47, 34),
    "Brown": (122, 78, 52),
    "Tan": (176, 122, 84),
    "Beige": (222, 176, 140),
    "Pink": (240, 170, 175),
}
HAIR_COLORS = {
    "Black": (25, 22, 22),
    "Brown": (92, 58, 33),
    "Blonde": (226, 196, 110),
    "Red": (170, 60, 35),
    "Gray": (175, 175, 180),
}
ONESIE_COLORS = {
    "Sky": (120, 180, 235),
    "Bubblegum": (240, 140, 180),
    "Mint": (130, 210, 170),
    "Sunny": (245, 205, 90),
    "Lilac": (180, 150, 230),
}
BABY_ACCESSORIES = ("None", "Bow", "Beanie", "Pacifier")

# name: (price, charm bonus)
PIERCINGS = {
    "Ear": (40, 4),
    "Eyebrow": (55, 6),
    "Lip": (60, 7),
    "Tongue": (70, 8),
    "Intimate": (100, 12),
}

CRAVINGS = ["pickles & ice cream", "chocolate-dipped fries", "spicy tacos",
            "a whole watermelon", "peanut butter & pickles", "extra-cheesy nachos"]


def piercing_label(name: str, kind: str) -> str:
    if name == "Intimate":
        return "Prince Albert" if kind == "penis" else "Hood piercing"
    return name


NAMES_M = ["Marlon", "Andre", "Diego", "Malik", "Jordan", "Theo", "Kai", "Ravi", "Luca", "Dante"]
NAMES_F = ["Nia", "Imani", "Zoe", "Lena", "Maya", "Aaliyah", "Sofia", "Jade", "Priya", "Chloe"]
VIBES = ["Charming", "Shy", "Wild", "Sweet", "Mysterious", "Funny", "Sporty", "Nerdy", "Flirty"]
BIOS = [
    "Looking for trouble. The good kind.",
    "Will steal your hoodie. And your heart.",
    "Gym, tacos, bad decisions.",
    "Swipe right if you can keep up.",
    "I make great pancakes the morning after.",
    "Here for a good time, not a long time.",
    "Dog lover. Night owl. Excellent kisser.",
    "Tell me your best pickup line.",
    "Just moved to Genitopia. Show me around?",
    "My love language is late-night texts.",
]


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


@dataclass
class Character:
    kind: str = "penis"
    name: str = "Brady"
    body_color: str = "Ebony"
    hair_color: str = "Black"
    accessory: str = ""          # NPC hats etc.


@dataclass
class Partner:
    name: str
    age: int  # always an adult
    anatomy: str  # "penis" or "vagina"
    vibe: str
    bio: str
    chemistry: float  # 0.3 - 1.0, scales how fun the night is
    sti_risk: float   # hidden chance of passing an infection without a condom
    skin: str = "Brown"
    hair: str = "Black"
    times: int = 0

    @property
    def label(self) -> str:
        return "Man" if self.anatomy == "penis" else "Woman"

    @property
    def look(self) -> Character:
        return Character(self.anatomy, self.name, self.skin, self.hair)

    @classmethod
    def random(cls, rng: random.Random, anatomy: str | None = None) -> "Partner":
        anatomy = anatomy or rng.choice(CHARACTER_TYPES)
        return cls(
            name=rng.choice(NAMES_M if anatomy == "penis" else NAMES_F),
            age=rng.randint(21, 45),
            anatomy=anatomy,
            vibe=rng.choice(VIBES),
            bio=rng.choice(BIOS),
            chemistry=round(rng.uniform(0.3, 1.0), 2),
            sti_risk=round(rng.uniform(0.03, 0.35), 2),
            skin=rng.choice(list(BODY_COLORS)),
            hair=rng.choice([h for h in HAIR_COLORS if h != "Gray"]),
        )


@dataclass
class Conception:
    day: int
    partner: str
    revealed: bool = False


@dataclass
class Baby:
    name: str = "Bean"
    skin: str = "Brown"
    hair: str = "Black"
    onesie: str = "Sky"
    accessory: str = "None"
    fullness: float = 80
    happiness: float = 80
    in_crib: bool = False
    crying: bool = False


@dataclass
class GameState:
    character: Character = field(default_factory=Character)
    rng: random.Random = field(default_factory=random.Random, repr=False)

    day: int = 1
    slot: int = 0  # index into TIME_SLOTS

    health: float = 100
    hygiene: float = 80
    energy: float = 80
    fullness: float = 70
    mood: float = 60
    money: int = 150
    condoms: int = 1
    formula: int = 0

    infection: str | None = None
    conception: Conception | None = None   # hidden until symptoms or a test
    in_labor: bool = False
    labor_days: int = 0
    craving: str | None = None
    baby: Baby | None = None
    baby_needs_setup: bool = False         # UI shows the customize-your-baby screen
    piercings: list[str] = field(default_factory=list)
    piercing_heal: int = 0                 # slots until the newest piercing heals

    matches: list[Partner] = field(default_factory=list)
    date: Partner | None = None            # who is expecting you at the Apartments
    swipes_today: int = 0
    show_me: str = "everyone"              # dating app filter: penis / vagina / everyone

    events: list = field(default_factory=list)   # active TownEvents (see events.py)
    raining: bool = False
    talks: dict = field(default_factory=dict)    # npc key -> times talked

    log: list[str] = field(default_factory=list)
    total_hookups: int = 0
    protected_hookups: int = 0
    infections_caught: int = 0
    game_over: bool = False
    end_reason: str = ""

    # ---- helpers -------------------------------------------------------
    @property
    def time_name(self) -> str:
        return TIME_SLOTS[self.slot]

    @property
    def is_night_time(self) -> bool:
        return self.slot >= 2

    @property
    def is_carrier(self) -> bool:
        """True when *you* are the one who is pregnant."""
        return self.character.kind == "vagina"

    @property
    def pregnancy_days(self) -> int:
        return self.day - self.conception.day if self.conception else -1

    @property
    def visibly_pregnant(self) -> bool:
        return self.pregnancy_days >= PREGNANCY_SHOWS_AFTER

    @property
    def belly_stage(self) -> int:
        """0-3: how big the bump is drawn (only for a pregnant vagina character)."""
        if not self.is_carrier or not self.conception:
            return 0
        d = self.pregnancy_days
        return 0 if d < PREGNANCY_SHOWS_AFTER else 1 if d < 7 else 2 if d < 10 else 3

    @property
    def baby_with_you(self) -> bool:
        return self.baby is not None and not self.baby.in_crib

    @property
    def charm(self) -> int:
        c = 20 + sum(PIERCINGS[p][1] for p in self.piercings) + self.mood / 5
        if self.hygiene >= 60:
            c += 10
        elif self.hygiene < 30:
            c -= 15
        return int(clamp(c))

    def say(self, msg: str) -> None:
        self.log.append(msg)
        del self.log[:-60]

    def adjust(self, **deltas: float) -> None:
        for stat, d in deltas.items():
            setattr(self, stat, clamp(getattr(self, stat) + d))

    def add_match(self, p: Partner) -> None:
        self.matches.append(p)
        del self.matches[:-8]

    def symptoms(self) -> list[str]:
        out = []
        if self.infection:
            out.append("Itching & burning. See a doctor!")
        if self.in_labor:
            out.append("IN LABOR! Get to the clinic!" if self.is_carrier
                       else f"{self.conception.partner} is in labor! Get to the clinic!")
        elif self.visibly_pregnant:
            out.append("Pregnant" if self.is_carrier else f"{self.conception.partner} is pregnant")
        if self.craving:
            who = "Craving" if self.is_carrier else f"{self.conception.partner} craves"
            out.append(f"{who}: {self.craving}")
        if self.piercing_heal:
            out.append("New piercing healing")
        if self.baby and self.baby.crying:
            out.append(f"{self.baby.name} is crying!")
        return out

    # ---- time ----------------------------------------------------------
    def advance(self, slots: int = 1) -> None:
        """Pass time: stats decay, conditions tick, days roll over."""
        from .events import maybe_spawn_event, tick_events  # local: avoids a cycle
        for _ in range(slots):
            if self.game_over:
                return
            self._tick()
            self.slot += 1
            if self.slot >= len(TIME_SLOTS):
                self.slot = 0
                self._new_day()
            tick_events(self)
            maybe_spawn_event(self)

    def _tick(self) -> None:
        tired = 2 if self.is_carrier and self.visibly_pregnant else 0
        self.adjust(fullness=-6, hygiene=-4, energy=-4 - tired)
        if self.fullness < 15:
            self.adjust(health=-5, mood=-4)
        if self.hygiene < 15:
            self.adjust(health=-2, mood=-3)
            if self.infection is None and self.rng.random() < 0.08:
                self._infect("Yeast infection" if self.character.kind == "vagina" else "Irritation infection")
                self.say("Poor hygiene caught up with you. Something itches...")
        if self.piercing_heal:
            self.piercing_heal -= 1
            if self.hygiene < 40 and self.infection is None and self.rng.random() < 0.15:
                self._infect("Infected piercing")
                self.say("Your new piercing is red and throbbing. Not the fun kind.")
        if self.energy < 10:
            self.adjust(health=-3, mood=-4)
        if self.infection:
            self.adjust(health=-4, mood=-2)
        if self.mood < 10:
            self.adjust(health=-2)
        if self.craving:
            self.adjust(mood=-3)
        if self.is_carrier and self.visibly_pregnant and not self.in_labor:
            roll = self.rng.random()
            if roll < 0.12:
                self.adjust(fullness=-15, health=-2, mood=-5)
                self.say("Morning sickness hits. You lose your lunch in a bush.")
            elif roll < 0.18:
                self.adjust(energy=-8, mood=-3)
                self.say("Your back aches and your feet are swollen. Pregnancy is a lot.")
        self._tick_baby()
        self._check_end()

    def _tick_baby(self) -> None:
        b = self.baby
        if not b:
            return
        b.fullness = clamp(b.fullness - 7)
        b.happiness = clamp(b.happiness - (2 if not b.in_crib else 6))
        was_crying = b.crying
        b.crying = b.fullness < 25 or b.happiness < 25
        if b.crying:
            self.adjust(mood=-4)
            if not was_crying:
                need = "hungry" if b.fullness < 25 else "lonely"
                self.say(f"{b.name} is wailing. Sounds {need}.")

    def _new_day(self) -> None:
        self.day += 1
        self.swipes_today = 0
        self.date = None  # dates don't wait overnight
        self._pregnancy_day()
        self._check_end()
        if not self.game_over and self.day > GAME_LENGTH_DAYS:
            self.game_over = True
            self.end_reason = f"You survived {GAME_LENGTH_DAYS} days in {TOWN_NAME}!"

    def _pregnancy_day(self) -> None:
        c = self.conception
        if not c:
            return
        days = self.day - c.day
        partner = c.partner
        if self.in_labor:
            self.labor_days += 1
            if self.labor_days >= 2:
                from .actions import deliver
                if self.is_carrier:
                    self.say("You couldn't make it to the clinic. The baby arrived at home! Ow.")
                    self.adjust(health=-20)
                else:
                    self.say(f"{partner} gave birth without you. \"You MISSED it.\" Ouch.")
                    self.adjust(mood=-20)
                deliver(self)
            return
        if days == PREGNANCY_SHOWS_AFTER:
            c.revealed = True
            if self.is_carrier:
                self.say("Your period is late, you're queasy and your belly feels... rounder. You're pregnant!")
            else:
                self.say(f"{partner} texts: \"hey... my period is late. I took a test. we're having a baby.\"")
            self.adjust(mood=-10)
        if days >= PREGNANCY_SHOWS_AFTER and self.craving is None and self.rng.random() < 0.6:
            self.craving = self.rng.choice(CRAVINGS)
            if self.is_carrier:
                self.say(f"You NEED {self.craving}. Right now. The Diner might have it.")
            else:
                self.say(f"{partner} texts: \"bring me {self.craving}. no questions.\"")
        if days >= LABOR_AFTER:
            self.in_labor = True
            self.labor_days = 0
            if self.is_carrier:
                self.say("Your water broke! Get to the Clinic NOW!")
            else:
                self.say(f"{partner}: \"IT'S TIME!!! Meet me at the Clinic!!\"")

    def _infect(self, name: str) -> None:
        self.infection = name
        self.infections_caught += 1

    def _check_end(self) -> None:
        if self.health <= 0 and not self.game_over:
            self.game_over = True
            self.end_reason = "Your health hit zero. Time to see a doctor in real life too!"

    # ---- scoring -------------------------------------------------------
    def score(self) -> int:
        days = min(self.day, GAME_LENGTH_DAYS)
        baby = (self.baby.happiness + self.baby.fullness) / 2 if self.baby else 0
        return int(days * 10 + self.mood + self.health + self.money / 5 + self.charm + baby
                   + self.protected_hookups * 15 - self.infections_caught * 40)
