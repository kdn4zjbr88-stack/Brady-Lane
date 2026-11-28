"""Player actions. Each returns None on success or a string explaining why it can't be done."""
from __future__ import annotations

from . import events
from .model import PIERCINGS, SWIPES_PER_DAY, Baby, Conception, GameState, Partner, piercing_label

CONDOM_PACK_PRICE = 15
CONDOM_PACK_SIZE = 3
MEAL_PRICE = 12
SNACK_PRICE = 5
DRINK_PRICE = 15
CLINIC_PRICE = 50
TEST_PRICE = 20
PILL_PRICE = 45
FORMULA_PRICE = 8
CHECKUP_PRICE = 20
WORK_PAY = 60

# Hidden per-encounter pregnancy odds (exaggerated a bit so choices matter in a 30-day game)
PREGNANCY_RISK = {"condom": 0.02, "pull_out": 0.06, "inside": 0.25}
STI_FACTOR = {"condom": 0.05, "pull_out": 1.0, "inside": 1.0}

STEAMY = [
    "{n} pulls you in by the collar. Clothes hit the floor. The neighbours definitely heard.",
    "One kiss turns into ten. The bed creaks. Neither of you cares.",
    "{n} whispers something filthy in your ear and the lights go out. Wow.",
    "Things get very steamy, very fast. {n} is grinning the whole time.",
    "You and {n} don't make it to the bed on the first try.",
]
FLIRTS = [
    "\"Are you always this cute or is it the lighting?\"",
    "\"I was hoping you'd come talk to me.\"",
    "\"Buy me a drink and I'll tell you a secret.\"",
    "\"You dance like you know what you're doing...\"",
]


# ---- basics ---------------------------------------------------------------
def eat(gs: GameState) -> str | None:
    if gs.money < MEAL_PRICE:
        return f"You need ${MEAL_PRICE} to eat."
    gs.money -= MEAL_PRICE
    gs.adjust(fullness=45, mood=6, health=2)
    gs.say("Burger, fries, shake. Absolutely worth it.")
    gs.advance()
    return None


def snack(gs: GameState) -> str | None:
    if gs.utilities_off:
        return "The fridge is dead. Pay your power bill."
    if gs.money < SNACK_PRICE:
        return f"Groceries cost ${SNACK_PRICE}."
    gs.money -= SNACK_PRICE
    gs.adjust(fullness=20, mood=2)
    gs.say("You raided the fridge.")
    return None


def shower(gs: GameState) -> str | None:
    if gs.utilities_off:
        return "No water! Pay your power & water bill."
    gs.hygiene = 100
    if "shower" in gs.upgrades:
        gs.adjust(mood=14, energy=5)
        gs.say("The rain shower is heavenly. You stand there for 40 minutes.")
    else:
        gs.adjust(mood=6)
        gs.say("Fresh and clean! Squeaky.")
    gs.advance()
    return None


def pee(gs: GameState) -> str | None:
    gs.adjust(mood=3)
    gs.say("Ahhh. Relief.")
    return None


def mirror(gs: GameState) -> str | None:
    if gs.charm >= 60:
        gs.say(f"Looking irresistible today. (Charm {gs.charm})")
    elif gs.charm >= 35:
        gs.say(f"Not bad at all. (Charm {gs.charm})")
    else:
        gs.say(f"Yikes. Maybe shower first? (Charm {gs.charm})")
    return None


def sleep(gs: GameState) -> str | None:
    gs.advance(4 - gs.slot)  # sleep through to next morning
    if gs.game_over:
        return None
    gs.energy = 100
    if "bed" in gs.upgrades:
        gs.adjust(health=15, mood=12, fullness=10)
    else:
        gs.adjust(health=8, mood=5, fullness=10)
    gs.say(f"You slept like a baby. Good morning, day {gs.day}!")
    return None


def work(gs: GameState) -> str | None:
    from .jobs import work as job_work
    return job_work(gs)


# ---- club -----------------------------------------------------------------
def drink(gs: GameState) -> str | None:
    if gs.is_carrier and gs.conception and gs.conception.revealed:
        return "Rocco: \"Not while you're expecting, hun. Mocktail?\""
    if gs.money < DRINK_PRICE:
        return f"Drinks are ${DRINK_PRICE}."
    gs.money -= DRINK_PRICE
    gs.adjust(mood=12, health=-2, fullness=3)
    gs.say("A strong drink. Your confidence goes up a notch.")
    return None


def dance(gs: GameState) -> str | None:
    if gs.energy < 15:
        return "Your legs say no."
    gs.adjust(mood=18, energy=-15, hygiene=-12)
    gs.say("You owned the dance floor. People are looking.")
    gs.advance()
    return None


def chat_up(gs: GameState, p: Partner) -> str | None:
    if p in gs.matches:
        return f"You already have {p.name}'s number."
    chance = 0.25 + gs.charm / 120 + p.chemistry * 0.2
    if gs.rng.random() < chance:
        gs.add_match(p)
        gs.adjust(mood=10)
        gs.say(f"{p.name}: {gs.rng.choice(FLIRTS)} You swapped numbers.")
    else:
        gs.adjust(mood=-8)
        gs.say(f"{p.name} smiled politely and turned back to their friends. Ouch.")
    return None


def go_home_with(gs: GameState, p: Partner) -> str | None:
    if p not in gs.matches:
        return "Get to know them first."
    gs.date = p
    gs.date_place = "apartments"
    gs.say(f"{p.name} grabs your hand: \"My place is right around the corner.\"")
    return None


# ---- dating app -----------------------------------------------------------
def new_profile(gs: GameState) -> Partner:
    anatomy = None if gs.show_me == "everyone" else gs.show_me
    return Partner.random(gs.rng, anatomy)


def swipe(gs: GameState, p: Partner, right: bool) -> bool | str:
    """Returns True on a match, False otherwise, or an error string."""
    if gs.swipes_today >= SWIPES_PER_DAY:
        return "Out of swipes today. Touch grass."
    gs.swipes_today += 1
    if not right:
        return False
    if gs.rng.random() < 0.2 + gs.charm / 150:
        gs.add_match(p)
        gs.say(f"It's a match with {p.name}! \"{p.bio}\"")
        return True
    return False


def text_match(gs: GameState, p: Partner) -> str | None:
    if not gs.is_night_time:
        gs.say(f"{p.name}: \"busy rn, text me tonight ;)\"")
        return None
    gs.date = p
    gs.date_place = "apartments"
    gs.say(f"{p.name}: \"come over. Apartments, unit 4. door's open.\"")
    return None


# ---- the bedroom ----------------------------------------------------------
def can_conceive(gs: GameState, p: Partner) -> bool:
    return gs.character.kind != p.anatomy


def hook_up(gs: GameState, p: Partner, method: str) -> str | None:
    """method: 'condom', 'pull_out' or 'inside'."""
    if gs.energy < 15:
        return "Too tired for that right now."
    if method == "condom" and gs.condoms <= 0:
        return "You're out of condoms. Hit the pharmacy."

    gs.total_hookups += 1
    p.times += 1
    fun = 15 + 25 * p.chemistry + gs.charm / 10
    gs.adjust(mood=fun, energy=-15, hygiene=-25)
    gs.say(gs.rng.choice(STEAMY).format(n=p.name))

    if method == "condom":
        gs.condoms -= 1
        gs.protected_hookups += 1
        gs.say("Wrapped up and worry-free.")
    elif method == "pull_out":
        gs.say("Pulled out in time... probably.")
    else:
        gs.say("No condom, no pulling out. Bold.")

    if gs.infection is None and gs.rng.random() < p.sti_risk * STI_FACTOR[method]:
        gs._infect(gs.rng.choice(["Chlamydia", "Gonorrhea", "Herpes flare-up", "Trichomoniasis"]))

    from .cycle import fertility
    risk = PREGNANCY_RISK[method] * (fertility(gs) if gs.is_carrier else 1.0)
    if can_conceive(gs, p) and gs.conception is None and gs.rng.random() < risk:
        gs.conception = Conception(day=gs.day, partner=p.name)  # hidden!

    gs.date = None
    from . import npcs, relationships
    npcs.after_hookup(gs, p)
    relationships.caught_cheating(gs, p.name)
    gs.advance()
    return None


# ---- shops ----------------------------------------------------------------
def buy_condoms(gs: GameState) -> str | None:
    if gs.money < CONDOM_PACK_PRICE:
        return f"Condoms cost ${CONDOM_PACK_PRICE}."
    gs.money -= CONDOM_PACK_PRICE
    gs.condoms += CONDOM_PACK_SIZE
    gs.say(f"Bought a {CONDOM_PACK_SIZE}-pack of condoms. Smart move.")
    return None


def pregnancy_test(gs: GameState) -> str | None:
    if gs.money < TEST_PRICE:
        return f"Tests cost ${TEST_PRICE}."
    gs.money -= TEST_PRICE
    c = gs.conception
    if c and gs.day - c.day >= 3:
        c.revealed = True
        gs.adjust(mood=-25)
        gs.say("Two lines. Positive. Oh no.")
    elif c:
        gs.say("Negative... though it might be too early to tell.")
    else:
        gs.say("Negative. Phew!")
    return None


def morning_after_pill(gs: GameState) -> str | None:
    if gs.money < PILL_PRICE:
        return f"The morning-after pill costs ${PILL_PRICE}."
    gs.money -= PILL_PRICE
    c = gs.conception
    if c and gs.day - c.day <= 1 and gs.rng.random() < 0.9:
        gs.conception = None
    who = "You take" if gs.character.kind == "vagina" else "You buy one for your partner. They take"
    gs.say(f"{who} the morning-after pill. Fingers crossed.")
    return None


def clinic(gs: GameState) -> str | None:
    if gs.time_name == "Night":
        return "The clinic is closed at night."
    if gs.money < CLINIC_PRICE:
        return f"A clinic visit costs ${CLINIC_PRICE}."
    gs.money -= CLINIC_PRICE
    if gs.infection:
        gs.say(f"Diagnosed: {gs.infection}. Treated! You feel better already.")
        gs.infection = None
        gs.adjust(health=15, mood=10)
    else:
        gs.say("Tested negative for everything. Clean bill of health!")
        gs.adjust(mood=8)
    gs.advance()
    return None


def piercing_price(gs: GameState, name: str) -> int:
    price = PIERCINGS[name][0]
    if events.active(gs, "flashsale") or gs.job == "apprentice":
        price //= 2
    return price


def get_piercing(gs: GameState, name: str) -> str | None:
    if name in gs.piercings:
        return "You already have that one."
    price = piercing_price(gs, name)
    if gs.money < price:
        return f"That piercing costs ${price}."
    gs.money -= price
    gs.piercings.append(name)
    gs.piercing_heal = 12
    gs.adjust(mood=10, health=-3)
    gs.say(f"New {piercing_label(name, gs.character.kind)} piercing! Ouch... but hot. "
           "Keep it clean while it heals.")
    gs.advance()
    return None


# ---- pregnancy ------------------------------------------------------------
def satisfy_craving(gs: GameState) -> str | None:
    if not gs.craving:
        return "No cravings right now."
    if gs.money < MEAL_PRICE:
        return f"That costs ${MEAL_PRICE}."
    gs.money -= MEAL_PRICE
    if gs.is_carrier:
        gs.adjust(fullness=40, mood=22)
        gs.say(f"Chef Bean whips up {gs.craving}. You inhale it. Pure bliss.")
    else:
        gs.adjust(mood=15)
        gs.say(f"You bring {gs.conception.partner} {gs.craving}. \"You're the best. Seriously.\"")
    gs.craving = None
    gs.advance()
    return None


def prenatal_checkup(gs: GameState) -> str | None:
    if gs.money < CHECKUP_PRICE:
        return f"A checkup costs ${CHECKUP_PRICE}."
    gs.money -= CHECKUP_PRICE
    gs.adjust(health=12, mood=10)
    d = gs.pregnancy_days
    gs.say(f"Dr. Ova: \"Strong heartbeat! About {d} days along. Eat well, rest, and no drinking.\"")
    gs.advance()
    return None


def deliver(gs: GameState) -> None:
    """The baby arrives. The UI then shows the customise-your-baby screen."""
    partner = gs.conception.partner if gs.conception else "your partner"
    gs.conception = None
    gs.in_labor = False
    gs.labor_days = 0
    gs.craving = None
    gs.baby = Baby(skin=gs.character.body_color, hair=gs.character.hair_color)
    gs.baby_needs_setup = True
    gs.formula += 2
    gs.adjust(mood=30)
    if gs.is_carrier:
        gs.adjust(health=-10, energy=-30)
    gs.say(f"It's a baby! You and {partner} are parents now. The clinic sends you home with 2 bottles of formula.")


def deliver_at_clinic(gs: GameState) -> str | None:
    if not gs.in_labor:
        return "Nobody's in labor."
    if gs.is_carrier:
        gs.say("Dr. Ova: \"Okay, PUSH!\" Hours of screaming later...")
    else:
        gs.say(f"You hold {gs.conception.partner}'s hand through the whole thing. They nearly break your fingers.")
    deliver(gs)
    gs.advance()
    return None


# ---- baby -----------------------------------------------------------------
def buy_formula(gs: GameState) -> str | None:
    if gs.money < FORMULA_PRICE:
        return f"Formula costs ${FORMULA_PRICE}."
    gs.money -= FORMULA_PRICE
    gs.formula += 2
    gs.say("Bought 2 bottles of baby formula.")
    return None


def feed_baby(gs: GameState) -> str | None:
    b = gs.baby
    if not b:
        return "You don't have a baby."
    if b.in_crib:
        return f"{b.name} is in the crib at home."
    if gs.formula <= 0:
        return "Out of formula! The Pharmacy sells it."
    gs.formula -= 1
    b.fullness = 100
    b.crying = b.happiness < 25
    gs.say(f"{b.name} gulps down a bottle and burps like a trucker.")
    return None


def cuddle_baby(gs: GameState) -> str | None:
    b = gs.baby
    if not b:
        return "You don't have a baby."
    if b.in_crib:
        return f"{b.name} is in the crib at home."
    b.happiness = 100
    b.crying = b.fullness < 25
    gs.adjust(mood=8)
    gs.say(f"You cuddle {b.name}. Tiny giggles. Your heart melts.")
    return None


def crib_baby(gs: GameState) -> str | None:
    b = gs.baby
    if not b:
        return "You don't have a baby."
    b.in_crib = not b.in_crib
    gs.say(f"You tuck {b.name} into the crib." if b.in_crib else f"You scoop {b.name} up. Off we go!")
    return None


# ---- period supplies --------------------------------------------------------
SUPPLIES_PRICE = 10
PAINKILLER_PRICE = 8


def buy_supplies(gs: GameState) -> str | None:
    if gs.money < SUPPLIES_PRICE:
        return f"Pads & tampons are ${SUPPLIES_PRICE}."
    gs.money -= SUPPLIES_PRICE
    gs.period_supplies += 6
    gs.say("Bought a box of pads & tampons (6).")
    return None


def buy_painkillers(gs: GameState) -> str | None:
    if gs.money < PAINKILLER_PRICE:
        return f"Painkillers are ${PAINKILLER_PRICE}."
    gs.money -= PAINKILLER_PRICE
    gs.painkillers += 3
    gs.say("Bought painkillers (3). Cramps, beware.")
    return None


# ---- ending a pregnancy ------------------------------------------------------
ABORTION_PILL_PRICE = 150
ABORTION_PROCEDURE_PRICE = 300
PILL_MAX_DAYS = 7
PROCEDURE_MAX_DAYS = 10


def abortion_options(gs: GameState) -> list[tuple[str, str, int, bool]]:
    """(method, label, price, available) for a pregnant player at the clinic."""
    d = gs.pregnancy_days
    return [("pill", "Medication abortion (pills)", ABORTION_PILL_PRICE, d <= PILL_MAX_DAYS),
            ("procedure", "In-clinic procedure", ABORTION_PROCEDURE_PRICE, d <= PROCEDURE_MAX_DAYS)]


def abortion(gs: GameState, method: str) -> str | None:
    c = gs.conception
    if not (gs.is_carrier and c and c.revealed):
        return "That's only an option when you know you're pregnant."
    if gs.in_labor:
        return "It's too late for that. The baby's coming!"
    _, label, price, ok = next(o for o in abortion_options(gs) if o[0] == method)
    if not ok:
        return "Dr. Ova: \"It's too far along for that option, I'm sorry.\""
    if gs.money < price:
        return f"Dr. Ova: \"That costs ${price}. We can help you look into payment options.\""
    gs.money -= price
    gs.conception = None
    gs.craving = None
    gs.cycle_day = 1
    if method == "pill":
        gs.adjust(health=-8, energy=-25, mood=-8)
        gs.say("Dr. Ova walks you through the pills and what to expect. You spend the day resting "
               "with a heating pad. \"Call me if anything worries you.\"")
    else:
        gs.adjust(health=-12, energy=-30, mood=-8)
        gs.say("The procedure is quick. Dr. Ova and the nurse are kind the whole time. "
               "\"Take it easy for a day or two. However you feel is okay.\"")
    gs.advance(2)
    return None
