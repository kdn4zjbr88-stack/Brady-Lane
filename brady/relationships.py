"""Going steady, getting engaged and getting married.

Your sweetheart can be a Genitopia resident (an Npc) or someone you met on Spark or at the club
(a Partner). Both have a .name and a .look, so everything here works with either.
"""
from __future__ import annotations

GIFTS = {  # name: (price, affection, shop)
    "Roses": (25, 8, "florist"),
    "Chocolates": (15, 5, "florist"),
    "Teddy bear": (35, 10, "florist"),
    "Necklace": (120, 25, "jeweler"),
}
RING_PRICE = 400
WEDDING_PRICE = 200
DAILY_SPOUSE_INCOME = 25


# ---- who is who ------------------------------------------------------------------------
def is_npc(who) -> bool:
    return hasattr(who, "key") and hasattr(who, "daily")


def npc(gs):
    """Your partner if they're a town resident (used for drawing them at home etc.)."""
    from .npcs import NPC_BY_KEY
    return NPC_BY_KEY.get(gs.partner_key) if gs.partner_key else None


def current(gs):
    """Your boyfriend/girlfriend/fiance(e)/spouse, resident or not."""
    if not gs.relationship:
        return None
    return npc(gs) or gs.partner_obj


def affection(gs, who) -> int:
    if is_npc(who):
        from .npcs import affection as npc_aff
        return npc_aff(gs, who)
    return gs.affection.get(f"p:{who.name}", int(30 + who.chemistry * 30))


def change(gs, who, amount: int) -> None:
    if is_npc(who):
        from .npcs import change_affection
        change_affection(gs, who, amount)
    else:
        gs.affection[f"p:{who.name}"] = max(0, min(100, affection(gs, who) + amount))


def title(who, rel: str) -> str:
    male = who.look.kind == "penis"
    return {"dating": "boyfriend" if male else "girlfriend",
            "engaged": "fiance" if male else "fiancee",
            "married": "husband" if male else "wife"}.get(rel, "")


def ask_word(who) -> str:
    return "boyfriend" if who.look.kind == "penis" else "girlfriend"


def is_partner(gs, who) -> bool:
    cur = current(gs)
    return cur is not None and cur.name == who.name


def _set_partner(gs, who) -> None:
    if is_npc(who):
        gs.partner_key, gs.partner_obj = who.key, None
    else:
        gs.partner_key, gs.partner_obj = None, who
    gs.relationship = "dating"
    gs.together_since = gs.last_partner_chat = gs.day


def _clear_partner(gs) -> None:
    gs.partner_key, gs.partner_obj, gs.relationship = None, None, ""


def can_ask(gs, who) -> bool:
    if is_npc(who) and who.decline:
        return False
    return not gs.relationship


# ---- asking someone out -------------------------------------------------------------------
def _accept(gs, who) -> None:
    _set_partner(gs, who)
    change(gs, who, 10)
    gs.adjust(mood=25)
    gs.say(f"{who.name}: \"YES! I'm your {title(who, 'dating')} now!\" It's official. Genitopia's newest couple.")


def _turn_down(gs, who, line: str) -> None:
    change(gs, who, -5)
    gs.adjust(mood=-6)
    gs.say(f"{who.name}: \"{line}\"")


def ask_out(gs, who) -> str | None:
    """Asking while talking normally: needs real affection."""
    if is_npc(who) and who.decline:
        return None
    if gs.relationship and not is_partner(gs, who):
        return "You're already in a relationship. Don't be that person."
    if is_partner(gs, who):
        return "You're already together!"
    if affection(gs, who) < 70:
        _turn_down(gs, who, "I really like you... but I'm not ready to be official yet.")
        return None
    _accept(gs, who)
    return None


def ask_after_hookup(gs, who) -> str | None:
    """Popping the question in bed. Chemistry and charm matter more than history here."""
    if not can_ask(gs, who):
        return "You're already in a relationship."
    times = getattr(who, "times", 1)
    if is_npc(who):
        chance = 0.25 + affection(gs, who) / 120 + gs.charm / 300
    else:
        chance = 0.3 + who.chemistry * 0.4 + gs.charm / 300 + (0.1 if times > 1 else 0)
    if gs.rng.random() < chance:
        _accept(gs, who)
    else:
        _turn_down(gs, who, gs.rng.choice([
            "Whoa, that was fun, but... let's not label it yet, okay?",
            "You're sweet. Ask me again after a few more nights like this.",
            "I'm not really looking for anything serious right now. But stay for breakfast?"]))
    return None


# ---- gifts, rings, proposals, weddings ------------------------------------------------------
def give_gift(gs, who, gift: str) -> str | None:
    if gs.gifts.get(gift, 0) <= 0:
        return f"You don't have any {gift.lower()}."
    gs.gifts[gift] -= 1
    bonus = GIFTS[gift][1] * (2 if is_partner(gs, who) else 1)
    change(gs, who, bonus)
    gs.adjust(mood=5)
    gs.say(f"You give {who.name} {gift.lower()}. They light up. (+{bonus} affection)")
    return None


def buy_gift(gs, gift: str) -> str | None:
    price = GIFTS[gift][0]
    if gs.money < price:
        return f"{gift} cost ${price}."
    gs.money -= price
    gs.gifts[gift] = gs.gifts.get(gift, 0) + 1
    gs.say(f"Bought {gift.lower()}. Now go give them to someone special.")
    return None


def buy_ring(gs) -> str | None:
    if gs.has_ring:
        return "You already have a ring burning a hole in your pocket."
    if gs.money < RING_PRICE:
        return f"The engagement ring is ${RING_PRICE}."
    gs.money -= RING_PRICE
    gs.has_ring = True
    gs.say("You buy a sparkling engagement ring. Your palms are already sweaty.")
    return None


def propose(gs, who) -> str | None:
    if not is_partner(gs, who) or gs.relationship != "dating":
        return "You need to be dating first."
    if not gs.has_ring:
        return "You need a ring! Rock Solid Jewelers has one."
    if gs.day - gs.together_since < 3:
        return "Whoa, slow down. You've only been together a couple of days."
    gs.has_ring = False
    if affection(gs, who) < 85:
        change(gs, who, -10)
        gs.adjust(mood=-20)
        gs.say(f"You drop to one knee. {who.name} panics: \"I... I need more time!\" They keep the ring though.")
        return None
    gs.relationship = "engaged"
    gs.adjust(mood=30)
    gs.say(f"You drop to one knee. {who.name} screams \"YES!\" and the whole town hears. You're engaged! "
           "Plan the wedding at Genitopia Chapel.")
    return None


def wedding(gs) -> str | None:
    who = current(gs)
    if gs.relationship != "engaged" or not who:
        return "You need to be engaged first."
    if gs.money < WEDDING_PRICE:
        return f"The wedding costs ${WEDDING_PRICE}."
    gs.money -= WEDDING_PRICE
    gs.relationship = "married"
    gs.adjust(mood=40, energy=-15)
    gs.say(f"Reverend Love: \"...I now pronounce you married!\" You kiss {who.name} as Granny Muffin sobs into "
           f"a hanky. {who.name} moves in with you. Rent is now split!")
    return None


# ---- everyday life -----------------------------------------------------------------------------
def caught_cheating(gs, other_name: str) -> bool:
    """Called after hooking up with someone who isn't your partner."""
    who = current(gs)
    if not who or who.name == other_name:
        return False
    chance = 0.6 if gs.relationship == "married" else 0.35
    if gs.rng.random() >= chance:
        return False
    change(gs, who, -60)
    word = title(who, gs.relationship)
    gs.say(f"{who.name} found out about {other_name}. \"We're DONE.\" Your {word} dumped you. Brutal.")
    gs.adjust(mood=-30)
    _clear_partner(gs)
    return True


def chat_with_partner(gs, who) -> None:
    if is_partner(gs, who):
        gs.last_partner_chat = gs.day


def new_day(gs) -> None:
    who = current(gs)
    if not who:
        return
    if gs.relationship == "married":
        gs.money += DAILY_SPOUSE_INCOME
        gs.adjust(mood=4)
        help_ = ""
        if gs.baby:
            gs.baby.fullness = max(gs.baby.fullness, 70)
            gs.baby.happiness = max(gs.baby.happiness, 70)
            help_ = f" They also did the night feed with {gs.baby.name}."
        gs.say(f"{who.name} made you breakfast and chipped in ${DAILY_SPOUSE_INCOME} for the household.{help_}")
        return
    if gs.day - gs.last_partner_chat >= 3:
        change(gs, who, -6)
        gs.say(f"{who.name} texts: \"Haven't seen you in days... do you even miss me?\"")
    else:
        msgs = ["\"good morning, cutie\"", "\"thinking about you ;)\"", "\"dinner tonight?\"", "\"miss your face\""]
        gs.say(f"{who.name} texts: {gs.rng.choice(msgs)}")
        gs.adjust(mood=3)
