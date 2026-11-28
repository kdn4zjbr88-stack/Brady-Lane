"""Going steady, getting engaged and getting married to a Genitopia resident."""
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


def npc(gs):
    from .npcs import NPC_BY_KEY
    return NPC_BY_KEY.get(gs.partner_key) if gs.partner_key else None


def title(n, rel: str) -> str:
    male = n.look.kind == "penis"
    return {"dating": "boyfriend" if male else "girlfriend",
            "engaged": "fiance" if male else "fiancee",
            "married": "husband" if male else "wife"}.get(rel, "")


def is_partner(gs, n) -> bool:
    return gs.partner_key == n.key and bool(gs.relationship)


def ask_out(gs, n) -> str | None:
    from .npcs import affection, change_affection
    if n.decline:
        return None
    if gs.partner_key and gs.partner_key != n.key:
        return "You're already in a relationship. Don't be that person."
    if is_partner(gs, n):
        return "You're already together!"
    if affection(gs, n) < 70:
        change_affection(gs, n, -5)
        gs.adjust(mood=-6)
        gs.say(f"{n.name}: \"I really like you... but I'm not ready to be official yet.\"")
        return None
    gs.partner_key, gs.relationship = n.key, "dating"
    gs.together_since = gs.last_partner_chat = gs.day
    change_affection(gs, n, 10)
    gs.adjust(mood=25)
    gs.say(f"{n.name}: \"YES! I'm your {title(n, 'dating')} now!\" It's official. Genitopia's newest couple.")
    return None


def give_gift(gs, n, gift: str) -> str | None:
    from .npcs import change_affection
    if gs.gifts.get(gift, 0) <= 0:
        return f"You don't have any {gift.lower()}."
    gs.gifts[gift] -= 1
    bonus = GIFTS[gift][1] * (2 if is_partner(gs, n) else 1)
    change_affection(gs, n, bonus)
    gs.adjust(mood=5)
    gs.say(f"You give {n.name} {gift.lower()}. They light up. (+{bonus} affection)")
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


def propose(gs, n) -> str | None:
    from .npcs import affection, change_affection
    if not is_partner(gs, n) or gs.relationship != "dating":
        return "You need to be dating first."
    if not gs.has_ring:
        return "You need a ring! Rock Solid Jewelers has one."
    if gs.day - gs.together_since < 3:
        return "Whoa, slow down. You've only been together a couple of days."
    gs.has_ring = False
    if affection(gs, n) < 85:
        change_affection(gs, n, -10)
        gs.adjust(mood=-20)
        gs.say(f"You drop to one knee. {n.name} panics: \"I... I need more time!\" They keep the ring though.")
        return None
    gs.relationship = "engaged"
    gs.adjust(mood=30)
    gs.say(f"You drop to one knee. {n.name} screams \"YES!\" and the whole town hears. You're engaged! "
           "Plan the wedding at Genitopia Chapel.")
    return None


def wedding(gs) -> str | None:
    n = npc(gs)
    if gs.relationship != "engaged" or not n:
        return "You need to be engaged first."
    if gs.money < WEDDING_PRICE:
        return f"The wedding costs ${WEDDING_PRICE}."
    gs.money -= WEDDING_PRICE
    gs.relationship = "married"
    gs.adjust(mood=40, energy=-15)
    gs.say(f"Reverend Love: \"...I now pronounce you married!\" You kiss {n.name} as Granny Muffin sobs into "
           f"a hanky. {n.name} moves in with you. Rent is now split!")
    return None


def caught_cheating(gs, other_name: str) -> bool:
    """Called after hooking up with someone who isn't your partner."""
    n = npc(gs)
    if not n or not gs.relationship or n.name == other_name:
        return False
    chance = 0.6 if gs.relationship == "married" else 0.35
    if gs.rng.random() >= chance:
        return False
    from .npcs import change_affection
    change_affection(gs, n, -60)
    word = title(n, gs.relationship)
    gs.say(f"{n.name} found out about {other_name}. \"We're DONE.\" Your {word} dumped you. Brutal.")
    gs.adjust(mood=-30)
    gs.partner_key, gs.relationship, gs.has_ring = None, "", gs.has_ring
    return True


def chat_with_partner(gs, n) -> None:
    if is_partner(gs, n):
        gs.last_partner_chat = gs.day


def new_day(gs) -> None:
    n = npc(gs)
    if not n or not gs.relationship:
        return
    from .npcs import change_affection
    if gs.relationship == "married":
        gs.money += DAILY_SPOUSE_INCOME
        gs.adjust(mood=4)
        gs.say(f"{n.name} made you breakfast and chipped in ${DAILY_SPOUSE_INCOME} for the household. Married life!")
        return
    if gs.day - gs.last_partner_chat >= 3:
        change_affection(gs, n, -6)
        gs.say(f"{n.name} texts: \"Haven't seen you in days... do you even miss me?\"")
    else:
        msgs = ["\"good morning, cutie\"", "\"thinking about you ;)\"", "\"dinner tonight?\"", "\"miss your face\""]
        gs.say(f"{n.name} texts: {gs.rng.choice(msgs)}")
        gs.adjust(mood=3)
