"""Core game state for Brady. No pygame imports here so logic stays testable."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

TIME_SLOTS = ["Morning", "Afternoon", "Evening", "Night"]
GAME_LENGTH_DAYS = 30

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

FIRST_NAMES = [
    "Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley", "Jamie",
    "Avery", "Quinn", "Drew", "Rowan", "Sky", "Dakota", "Reese", "Blake",
    "Marlon", "Nia", "Andre", "Zoe", "Malik", "Imani", "Diego", "Lena",
]
VIBES = ["Charming", "Shy", "Wild", "Sweet", "Mysterious", "Funny", "Sporty", "Nerdy"]


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


@dataclass
class Partner:
    name: str
    age: int  # always an adult
    vibe: str
    chemistry: float  # 0.3 - 1.0, scales how fun the night is
    sti_risk: float   # hidden chance of passing an infection if unprotected
    times: int = 0

    @classmethod
    def random(cls, rng: random.Random) -> "Partner":
        return cls(
            name=rng.choice(FIRST_NAMES),
            age=rng.randint(21, 45),
            vibe=rng.choice(VIBES),
            chemistry=round(rng.uniform(0.3, 1.0), 2),
            sti_risk=round(rng.uniform(0.03, 0.35), 2),
        )


@dataclass
class Character:
    kind: str = "penis"
    name: str = "Brady"
    body_color: str = "Ebony"
    hair_color: str = "Black"


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
    money: int = 100
    condoms: int = 1

    infection: str | None = None
    scare_days: int = 0          # >0 while waiting out a pregnancy scare
    partners: list[Partner] = field(default_factory=list)
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

    def say(self, msg: str) -> None:
        self.log.append(msg)
        del self.log[:-50]

    def adjust(self, **deltas: float) -> None:
        for stat, d in deltas.items():
            setattr(self, stat, clamp(getattr(self, stat) + d))

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
                self._infect("Yeast/irritation infection" if self.character.kind == "vagina"
                             else "Irritation infection")
                self.say("Poor hygiene caught up with you. Something itches...")
        if self.energy < 10:
            self.adjust(health=-3, mood=-4)
        if self.infection:
            self.adjust(health=-4, mood=-2)
        if self.mood < 10:
            self.adjust(health=-2)
        self._check_end()

    def _new_day(self) -> None:
        self.day += 1
        if self.scare_days > 0:
            self.scare_days -= 1
            if self.scare_days == 0:
                self.say("Pregnancy scare is over: false alarm. Phew! Maybe use protection next time.")
                self.adjust(mood=15)
            else:
                self.adjust(mood=-8)
                self.say("Still anxiously waiting on that pregnancy scare...")
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
        safe_bonus = self.protected_hookups * 15
        return int(days * 10 + self.mood + self.health + self.money / 5
                   + safe_bonus - self.infections_caught * 40)
