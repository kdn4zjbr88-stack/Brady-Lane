"""Core game state for Brady. No pygame imports here so logic stays testable."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

TIME_SLOTS = ["Morning", "Afternoon", "Evening", "Night"]
GAME_LENGTH_DAYS = 30
PREGNANCY_SHOWS_AFTER = 4     # days until a missed period shows up
PREGNANCY_ENDING_AFTER = 8    # days until it becomes the game's ending
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
}

# name: (price, charm bonus)
PIERCINGS = {
    "Ear": (40, 4),
    "Eyebrow": (55, 6),
    "Lip": (60, 7),
    "Tongue": (70, 8),
    "Intimate": (100, 12),
}


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
    "Just moved here. Show me around?",
    "My love language is late-night texts.",
]


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


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
            hair=rng.choice(list(HAIR_COLORS)),
        )


@dataclass
class Character:
    kind: str = "penis"
    name: str = "Brady"
    body_color: str = "Ebony"
    hair_color: str = "Black"


@dataclass
class Conception:
    day: int
    partner: str
    revealed: bool = False


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

    infection: str | None = None
    conception: Conception | None = None   # hidden until symptoms or a test
    piercings: list[str] = field(default_factory=list)
    piercing_heal: int = 0                 # slots until the newest piercing heals

    matches: list[Partner] = field(default_factory=list)
    date: Partner | None = None            # who is expecting you at the Apartments
    swipes_today: int = 0
    show_me: str = "everyone"              # dating app filter: penis / vagina / everyone

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
    def charm(self) -> int:
        c = 20 + sum(PIERCINGS[p][1] for p in self.piercings) + self.mood / 5
        if self.hygiene >= 60:
            c += 10
        elif self.hygiene < 30:
            c -= 15
        return int(clamp(c))

    def say(self, msg: str) -> None:
        self.log.append(msg)
        del self.log[:-50]

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
        c = self.conception
        if c and self.day - c.day >= PREGNANCY_SHOWS_AFTER:
            out.append("Period is late..." if self.character.kind == "vagina"
                       else f"{c.partner}'s period is late...")
        if self.piercing_heal:
            out.append("New piercing healing: keep it clean")
        return out

    # ---- time ----------------------------------------------------------
    def advance(self, slots: int = 1) -> None:
        """Pass time: stats decay, conditions tick, days roll over."""
        for _ in range(slots):
            if self.game_over:
                return
            self._tick()
            self.slot += 1
            if self.slot >= len(TIME_SLOTS):
                self.slot = 0
                self._new_day()

    def _tick(self) -> None:
        self.adjust(fullness=-6, hygiene=-4, energy=-4)
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
        self._check_end()

    def _new_day(self) -> None:
        self.day += 1
        self.swipes_today = 0
        self.date = None  # dates don't wait overnight
        c = self.conception
        if c:
            days = self.day - c.day
            if days == PREGNANCY_SHOWS_AFTER:
                if self.character.kind == "vagina":
                    self.say("Your period is late. Maybe grab a pregnancy test...")
                else:
                    self.say(f"{c.partner} texts: \"hey... my period is late. we need to talk.\"")
                self.adjust(mood=-15)
            elif days >= PREGNANCY_ENDING_AFTER and not self.game_over:
                self.game_over = True
                self.end_reason = "Baby on the way! Your carefree days are over."
        self._check_end()
        if not self.game_over and self.day > GAME_LENGTH_DAYS:
            self.game_over = True
            self.end_reason = f"You survived {GAME_LENGTH_DAYS} days!"

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
        return int(days * 10 + self.mood + self.health + self.money / 5 + self.charm
                   + self.protected_hookups * 15 - self.infections_caught * 40)
