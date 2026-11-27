"""Baseball, Genitopia's favourite sport: the Ballers, their schedule and the batting mini-game."""
from __future__ import annotations

from dataclasses import dataclass, field

TEAM = "Genitopia Ballers"
OPPONENTS = ["Scrotum City Sluggers", "Labia Lakes Lumberjacks", "Pubeville Pirates",
             "Shaft Falls Hammers", "Nippleton Knights", "Cervix Springs Comets"]
TICKET = 12
PRACTICE = 5


def is_game_day(gs) -> bool:
    return gs.day % 3 == 0


def next_game_day(gs) -> int:
    if is_game_day(gs) and gs.slot <= 2 and not gs.played_today:
        return gs.day
    d = gs.day + 1
    while d % 3:
        d += 1
    return d


def opponent(gs) -> str:
    return OPPONENTS[(gs.day // 3) % len(OPPONENTS)]


def game_on(gs) -> bool:
    """The game is played in the evening of a game day."""
    return is_game_day(gs) and gs.slot == 2


def record(gs) -> str:
    return f"{gs.team_wins}-{gs.team_losses}"


def finish_game(gs, ballers: int, them: int, you_played: bool) -> None:
    opp = opponent(gs)
    won = ballers > them
    if won:
        gs.team_wins += 1
    else:
        gs.team_losses += 1
    gs.last_game = f"{'beat' if won else 'lost to'} the {opp} {ballers}-{them}"
    gs.played_today = True
    if you_played:
        gs.fame = min(30, gs.fame + (4 if won else 1))
        if won:
            gs.money += 50
            gs.adjust(mood=20)
            gs.say(f"WIN! The Ballers {gs.last_game}. The crowd chants your name. +$50 bonus.")
        else:
            gs.adjust(mood=-8)
            gs.say(f"The Ballers {gs.last_game}. Coach Rod: \"We'll get 'em next time.\"")
    else:
        gs.say(f"Final score: the Ballers {gs.last_game}. Season record: {record(gs)}.")


def simulate_if_missed(gs) -> None:
    """Called as the evening ends: if nobody played, the game happens without you."""
    if is_game_day(gs) and not gs.played_today:
        b, t = gs.rng.randint(1, 8), gs.rng.randint(1, 8)
        if b == t:
            b += 1
        finish_game(gs, b, t, you_played=False)


def watch_game(gs) -> str | None:
    if not game_on(gs):
        return "No game right now. Games are on the evening of every 3rd day."
    if gs.money < TICKET:
        return f"Tickets are ${TICKET}."
    if not (gs.job == "concessions"):
        gs.money -= TICKET
    b, t = gs.rng.randint(1, 8), gs.rng.randint(1, 8)
    if b == t:
        b += 1
    gs.adjust(mood=12, fullness=10)
    gs.say("You grab a hot dog and cheer from the bleachers.")
    finish_game(gs, b, t, you_played=False)
    gs.adjust(mood=10 if b > t else -4)
    gs.advance()
    return None


# ---- batting mini-game ----------------------------------------------------------
PITCHES = {"Fastball": 0.72, "Changeup": 1.15, "Curveball": 0.95}
SWEET = 0.93


@dataclass
class AtBat:
    mode: str                     # "practice" or "game"
    pitches_left: int = 10        # practice
    at_bats_left: int = 4         # game
    strikes: int = 0
    balls: int = 0
    hits: list = field(default_factory=list)   # "single", "double", "homer", "walk"
    pitch: str = "Fastball"
    is_strike: bool = True
    swung: bool = False
    result: str = ""

    @property
    def done(self) -> bool:
        return self.pitches_left <= 0 if self.mode == "practice" else self.at_bats_left <= 0

    def new_pitch(self, rng) -> None:
        self.pitch = rng.choice(list(PITCHES))
        self.is_strike = rng.random() < 0.72
        self.swung = False
        self.result = ""


def judge_swing(ab: AtBat, t: float) -> str:
    """t = 0..1 is how far the pitch has travelled when you swing (1 = at the plate)."""
    off = abs(t - SWEET)
    quality = max(0.0, 1 - off / 0.14)
    if not ab.is_strike:
        quality *= 0.55
    if quality > 0.82:
        return "homer"
    if quality > 0.55:
        return "double"
    if quality > 0.28:
        return "single"
    if quality > 0.08:
        return "foul"
    return "miss"


def resolve(ab: AtBat, outcome: str) -> str:
    """Apply a pitch outcome ('homer', 'double', 'single', 'foul', 'miss', 'taken').

    Returns the text shown to the player.
    """
    text = {"homer": "HOME RUN!", "double": "Double!", "single": "Base hit!", "foul": "Foul ball",
            "miss": "Swing and a miss!"}.get(outcome, "")
    end_at_bat = False
    if outcome in ("homer", "double", "single"):
        ab.hits.append(outcome)
        end_at_bat = True
    elif outcome == "foul":
        ab.strikes = min(2, ab.strikes + 1)
    elif outcome == "miss":
        ab.strikes += 1
    elif outcome == "taken":
        if ab.is_strike:
            ab.strikes += 1
            text = "Called strike!"
        else:
            ab.balls += 1
            text = "Ball."
    if ab.strikes >= 3:
        text += "  Strike three, you're out!" if text else "Strikeout!"
        end_at_bat = True
    if ab.balls >= 4:
        ab.hits.append("walk")
        text = "Ball four. Take your base!"
        end_at_bat = True
    if ab.mode == "practice":
        ab.pitches_left -= 1
        if end_at_bat:
            ab.strikes = ab.balls = 0
    elif end_at_bat:
        ab.at_bats_left -= 1
        ab.strikes = ab.balls = 0
    ab.result = text
    return text


def finish(gs, ab: AtBat) -> None:
    hits = ab.hits
    homers = hits.count("homer")
    if ab.mode == "practice":
        gs.adjust(mood=4 + 2 * homers, energy=-10)
        gs.fame = min(30, gs.fame + (1 if homers else 0))
        gs.say(f"Batting practice: {len([h for h in hits if h != 'walk'])} hits, {homers} homers.")
        gs.advance()
        return
    runs = homers * 2 + hits.count("double") + hits.count("single") * 0.6 + hits.count("walk") * 0.3
    ballers = int(gs.rng.randint(0, 4) + runs)
    them = gs.rng.randint(1, 7)
    if ballers == them:
        ballers += 1 if runs >= 1.5 else -1
        ballers = max(0, ballers)
        if ballers == them:
            them += 1
    gs.adjust(energy=-20, hygiene=-15)
    finish_game(gs, ballers, them, you_played=True)
    gs.advance()
