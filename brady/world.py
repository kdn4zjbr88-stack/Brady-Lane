"""Map data for Genitopia: the walkable town and each building's interior."""
from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Rect


@dataclass
class Furniture:
    rect: Rect
    kind: str               # picks the painter in scenery.py
    solid: bool = True
    occlude: bool = False   # drawn in front of characters standing behind it
    upgrade: str = ""       # tied to a house upgrade...
    alt: str = ""           # ...if set, this kind is used once owned; if empty, it only exists once owned

    def present(self, upgrades) -> bool:
        return not self.upgrade or self.alt or self.upgrade in upgrades

    def kind_for(self, upgrades) -> str:
        return self.alt if self.upgrade and self.alt and self.upgrade in upgrades else self.kind


@dataclass
class Hotspot:
    key: str          # what the interaction is, e.g. "shower" or "door:club"
    zone: Rect        # standing inside this triggers the pop-up
    title: str
    npc: str = ""     # shopkeeper attached to this spot (adds a "Chat" option)
    upgrade: str = "" # only exists once this house upgrade is owned


@dataclass
class Building:
    key: str
    name: str
    rect: Rect
    wall: tuple
    roof: tuple
    door_side: str    # "bottom" or "top"
    awning: tuple | None = None

    @property
    def door(self) -> Rect:
        d = Rect(0, 0, 64, 70 if self.door_side == "bottom" else 14)
        if self.door_side == "bottom":
            d.midbottom = self.rect.midbottom
        else:
            d.midtop = self.rect.midtop
        return d

    @property
    def door_zone(self) -> Rect:
        z = Rect(0, 0, 120, 84)
        if self.door_side == "bottom":
            z.midtop = self.rect.midbottom
        else:
            z.midbottom = self.rect.midtop
        return z

    @property
    def outside_spot(self) -> tuple[int, int]:
        return self.door_zone.center


@dataclass
class Room:
    key: str
    name: str
    size: tuple[int, int]
    floor: str               # wood / tile / carpet / club / lino / diner
    wall: tuple
    spawn: tuple[int, int]
    furniture: list[Furniture] = field(default_factory=list)
    hotspots: list[Hotspot] = field(default_factory=list)

    def solids(self, upgrades=()) -> list[Rect]:
        return [f.rect for f in self.furniture if f.solid and f.present(upgrades)]

    def spots(self, upgrades=()) -> list[Hotspot]:
        return [h for h in self.hotspots if not h.upgrade or h.upgrade in upgrades]


def _spot(key, rect, title, pad=55, npc="", upgrade=""):
    return Hotspot(key, rect.inflate(pad * 2, pad * 2), title, npc, upgrade)


# ---- town -------------------------------------------------------------------
TOWN_SIZE = (3500, 2500)
ROADS = [Rect(0, 760, 3500, 120), Rect(0, 1640, 3500, 120), Rect(1240, 0, 120, 2500), Rect(2640, 0, 120, 2500)]
SIDEWALKS = [Rect(0, 732, 3500, 28), Rect(0, 880, 3500, 28), Rect(0, 1612, 3500, 28), Rect(0, 1760, 3500, 28),
             Rect(1212, 0, 28, 2500), Rect(1360, 0, 28, 2500), Rect(2612, 0, 28, 2500), Rect(2760, 0, 28, 2500)]

BUILDINGS = [
    Building("home", "Home", Rect(200, 300, 360, 320), (200, 170, 140), (120, 70, 60), "bottom"),
    Building("diner", "Bean's Diner", Rect(700, 380, 300, 240), (235, 225, 200), (190, 55, 55), "bottom",
             (200, 50, 50)),
    Building("office", "Office", Rect(1500, 260, 380, 360), (165, 175, 190), (80, 90, 110), "bottom"),
    Building("pharmacy", "Pharmacy", Rect(2020, 380, 300, 240), (240, 245, 245), (40, 150, 90), "bottom",
             (40, 160, 90)),
    Building("club", "Club Velvet", Rect(200, 1000, 440, 340), (70, 40, 85), (40, 20, 50), "top"),
    Building("studio", "Ink & Steel", Rect(760, 1000, 300, 260), (85, 85, 92), (35, 35, 40), "top",
             (30, 30, 30)),
    Building("clinic", "Genitopia General", Rect(1500, 1000, 340, 300), (238, 242, 248), (60, 120, 200), "top"),
    Building("apartments", "Apartments", Rect(1980, 1000, 420, 400), (180, 120, 95), (95, 60, 50), "top"),
    Building("ballpark", "Ballers Stadium", Rect(420, 1880, 700, 520), (205, 200, 190), (40, 90, 160), "top"),
    Building("hardware", "Screw & Nail", Rect(1880, 1880, 380, 280), (190, 160, 120), (210, 110, 40), "top",
             (230, 120, 40)),
    Building("jeweler", "Rock Solid", Rect(2840, 380, 280, 240), (70, 68, 90), (200, 160, 60), "bottom",
             (40, 40, 60)),
    Building("florist", "Petal Pushers", Rect(3180, 380, 280, 240), (245, 230, 235), (220, 120, 160), "bottom",
             (230, 130, 170)),
    Building("petshop", "Nuts & Eggs", Rect(2840, 1000, 300, 260), (240, 220, 170), (90, 160, 200), "top",
             (90, 170, 210)),
    Building("boutique", "Birthday Suits", Rect(3180, 1000, 280, 260), (40, 38, 46), (230, 80, 140), "top",
             (230, 80, 140)),
    Building("chapel", "Genitopia Chapel", Rect(2840, 1880, 320, 380), (248, 246, 240), (120, 90, 160), "top"),
    Building("gym", "Pump House Gym", Rect(3200, 1880, 260, 300), (85, 85, 95), (210, 60, 50), "top"),
]
BUILDING_BY_KEY = {b.key: b for b in BUILDINGS}

TREES = [(120, 120), (640, 160), (1120, 220), (1980, 140), (2480, 260), (1140, 620), (2480, 640),
         (120, 1500), (700, 1460), (1150, 1120), (1420, 1560), (1920, 1580), (2520, 1580),
         (1110, 1580), (980, 120), (2440, 1250), (200, 2000), (220, 2380), (1600, 1980), (1640, 2380),
         (2460, 1960), (2440, 2380), (1180, 2300), (3460, 160), (2860, 690), (3440, 690), (2860, 1500),
         (3200, 1520), (3460, 1480), (2820, 2420), (3460, 2420)]
FOUNTAIN = (1660, 1500, 70)       # x, y, radius
BENCHES = [(1560, 1430), (1760, 1430), (640, 922)]
LAMPS = ([(x, 730) for x in range(160, 3500, 320)] + [(x, 910) for x in range(320, 3500, 320)]
         + [(x, 1610) for x in range(160, 3500, 320)] + [(x, 1790) for x in range(320, 3500, 320)])
FLOWERBEDS = [Rect(220, 630, 90, 22), Rect(450, 630, 90, 22), Rect(2040, 630, 80, 22),
              Rect(2220, 630, 80, 22), Rect(1520, 972, 90, 22), Rect(1730, 972, 90, 22),
              Rect(1900, 1852, 90, 22), Rect(2150, 1852, 90, 22), Rect(2860, 630, 80, 22),
              Rect(3200, 630, 80, 22), Rect(3360, 630, 80, 22), Rect(2860, 1852, 80, 22), Rect(3080, 1852, 80, 22)]
WELCOME_SIGN = Rect(40, 640, 150, 70)


def town_solids() -> list[Rect]:
    solids = [b.rect for b in BUILDINGS]
    solids += [Rect(x - 10, y - 6, 20, 16) for x, y in TREES]          # trunks
    fx, fy, fr = FOUNTAIN
    solids.append(Rect(fx - fr, fy - fr * 0.6, fr * 2, fr * 1.2))
    solids.append(Rect(WELCOME_SIGN.x, WELCOME_SIGN.bottom - 12, WELCOME_SIGN.w, 12))
    return solids


# ---- interiors --------------------------------------------------------------
def F(x, y, w, h, kind, solid=True, occlude=False):
    return Furniture(Rect(x, y, w, h), kind, solid, occlude)


def _home():
    bed, crib, mirror = Rect(60, 80, 240, 160), Rect(330, 80, 110, 84), Rect(480, 6, 80, 40)
    fridge, kitchen = Rect(60, 590, 90, 130), Rect(150, 640, 180, 80)
    shower, toilet = Rect(1010, 40, 160, 150), Rect(1090, 310, 70, 70)
    tv, gym, tub = Rect(440, 250, 200, 36), Rect(60, 330, 180, 130), Rect(870, 500, 280, 200)
    return Room("home", "Home", (1200, 760), "wood", (215, 200, 180), (600, 690), [
        F(820, 0, 380, 760, "tilefloor", solid=False),
        F(360, 330, 320, 190, "rug", solid=False),
        Furniture(bed, "bed", upgrade="bed", alt="bed_luxe"),
        Furniture(crib, "crib", upgrade="nursery", alt="crib_nursery"),
        Furniture(mirror, "mirror", solid=False),
        Furniture(fridge, "fridge"),
        Furniture(kitchen, "kitchen", upgrade="kitchen", alt="kitchen_pro"),
        F(410, 560, 260, 90, "couch"),
        Furniture(tv, "tv", upgrade="tv"),
        Furniture(gym, "gym", upgrade="gym"),
        F(800, 0, 20, 280, "wall"),
        F(800, 380, 20, 380, "wall"),
        Furniture(shower, "shower", upgrade="shower", alt="shower_rain"),
        Furniture(toilet, "toilet"),
        F(860, 30, 70, 50, "sink"),
        Furniture(tub, "hottub", upgrade="hottub"),
        F(730, 690, 44, 44, "plant"),
    ], [
        _spot("sleep", bed, "Your bed"),
        _spot("crib", crib, "Crib", 45),
        _spot("mirror", Rect(480, 30, 80, 20), "Mirror", 40),
        _spot("snack", fridge, "Fridge"),
        _spot("cook", kitchen, "Chef's kitchen", 45, upgrade="kitchen"),
        _spot("tv", tv, "Giant TV", 60, upgrade="tv"),
        _spot("gym", gym, "Home gym", 45, upgrade="gym"),
        _spot("shower", shower, "Bathroom: shower"),
        _spot("pee", toilet, "Bathroom: toilet", 40),
        _spot("hottub", tub, "Hot tub", 50, upgrade="hottub"),
    ])


def _club():
    floor, bar = Rect(420, 210, 420, 320), Rect(60, 150, 280, 60)
    return Room("club", "Club Velvet", (1200, 760), "club", (50, 25, 60), (600, 680), [
        Furniture(floor, "dancefloor", solid=False),
        Furniture(bar, "bar", occlude=True),
        F(520, 30, 220, 80, "dj"),
        F(1000, 140, 160, 100, "vip"),
        F(1000, 480, 160, 100, "vip"),
        F(80, 420, 120, 120, "loungetable"),
        F(60, 640, 44, 44, "plant"),
        F(1100, 650, 44, 44, "plant"),
    ], [
        Hotspot("dance", floor, "Dance floor"),
        _spot("bar", bar, "Bar", 60, npc="rocco"),
    ])


def _diner():
    counter = Rect(100, 170, 700, 56)
    return Room("diner", "Bean's Diner", (900, 600), "diner", (230, 215, 195), (450, 490), [
        Furniture(counter, "counter_red", occlude=True),
        F(120, 30, 660, 40, "menuboard", solid=False),
        *[F(x, 238, 30, 30, "stool", solid=False) for x in range(160, 760, 90)],
        F(130, 360, 130, 90, "table"),
        F(640, 360, 130, 90, "table"),
        F(385, 380, 130, 90, "table"),
    ], [_spot("eat", counter, "Diner counter", npc="chef")])


def _office():
    desk = Rect(370, 260, 160, 70)
    return Room("office", "Office", (900, 600), "lino", (200, 205, 215), (450, 490), [
        Furniture(desk, "desk", occlude=True),
        F(80, 130, 150, 70, "desk", occlude=True),
        F(670, 130, 150, 70, "desk", occlude=True),
        F(800, 400, 44, 70, "cooler"),
        F(60, 480, 44, 44, "plant"),
        F(330, 20, 240, 30, "whiteboard", solid=False),
    ], [_spot("work", desk, "Your desk"), _spot("talk:boss", Rect(80, 130, 150, 70), "Boss Richard", 50)])


def _pharmacy():
    counter = Rect(150, 150, 500, 56)
    return Room("pharmacy", "Pharmacy", (800, 560), "tile", (235, 245, 240), (400, 450), [
        Furniture(counter, "counter_green", occlude=True),
        F(170, 20, 460, 60, "shelf_back", solid=False),
        F(50, 290, 40, 200, "shelf"),
        F(710, 290, 40, 200, "shelf"),
    ], [_spot("pharmacy", counter, "Pharmacy counter", npc="patty")])


def _clinic():
    desk = Rect(300, 170, 200, 70)
    return Room("clinic", "Genitopia General", (800, 560), "lino", (225, 238, 248), (400, 450), [
        Furniture(desk, "desk_white", occlude=True),
        F(590, 50, 170, 80, "exambed"),
        F(50, 300, 120, 50, "bench"),
        F(50, 400, 120, 50, "bench"),
        F(710, 470, 44, 44, "plant"),
    ], [_spot("clinic", desk, "Dr. Ova", npc="ova")])


def _studio():
    chair = Rect(350, 210, 100, 110)
    return Room("studio", "Ink & Steel", (800, 560), "dark", (60, 58, 66), (400, 450), [
        Furniture(chair, "piercechair"),
        F(60, 40, 220, 50, "display"),
        F(520, 40, 220, 50, "display"),
        F(60, 330, 40, 160, "shelf"),
    ], [_spot("studio", chair, "Piercing chair", npc="pierce")])


def _apartment():
    bed = Rect(580, 80, 260, 180)
    return Room("apartments", "Their bedroom", (900, 600), "carpet", (190, 160, 175), (450, 470), [
        F(330, 300, 280, 170, "rug", solid=False),
        Furniture(bed, "bed_red"),
        F(60, 40, 140, 60, "dresser"),
        F(60, 380, 170, 90, "couch"),
        F(820, 500, 44, 44, "plant"),
    ], [_spot("bed", bed, "Their bed", 70)])


def _ballpark():
    cage, stand = Rect(1120, 560, 220, 230), Rect(60, 600, 240, 90)
    return Room("ballpark", "Ballers Stadium", (1400, 900), "field", (60, 110, 70), (700, 840), [
        F(450, 300, 500, 460, "diamond", solid=False),
        F(60, 70, 1280, 150, "bleachers"),
        F(560, 4, 280, 56, "scoreboard", solid=False),
        F(150, 300, 200, 60, "dugout"),
        Furniture(cage, "cage"),
        Furniture(stand, "concession", occlude=True),
    ], [
        _spot("plate", Rect(670, 700, 60, 30), "Home plate", 50),
        _spot("cage", cage, "Batting cage", 40),
        Hotspot("bleachers", Rect(380, 220, 640, 70), "Bleachers"),
        _spot("concession", stand, "Concessions", 50),
    ])


def _hardware():
    counter = Rect(150, 150, 500, 56)
    return Room("hardware", "Screw & Nail", (800, 560), "lino", (230, 215, 190), (400, 450), [
        Furniture(counter, "counter_orange", occlude=True),
        F(170, 18, 460, 64, "toolwall", solid=False),
        F(50, 290, 170, 130, "hottub"),
        F(580, 300, 170, 110, "bed_luxe"),
    ], [_spot("hardware", counter, "Screw & Nail", npc="mandy")])


def _shop(key, name, floor, wall, counter_kind, spot_title, npc, displays):
    counter = Rect(150, 150, 500, 56)
    return Room(key, name, (800, 560), floor, wall, (400, 450), [
        Furniture(counter, counter_kind, occlude=True),
        *[F(x, y, w, h, kind) for x, y, w, h, kind in displays],
    ], [_spot(key, counter, spot_title, npc=npc)])


def _chapel():
    altar = Rect(330, 110, 240, 50)
    pews = [F(x, y, 300, 40, "pew") for y in range(260, 560, 80) for x in (80, 520)]
    return Room("chapel", "Genitopia Chapel", (900, 700), "carpet_aisle", (240, 235, 225), (450, 640), [
        F(400, 64, 100, 600, "aisle", solid=False),
        Furniture(altar, "altar", occlude=True),
        F(120, 70, 60, 120, "stainedglass", solid=False),
        F(720, 70, 60, 120, "stainedglass", solid=False),
        *pews,
    ], [_spot("chapel", altar, "Genitopia Chapel", 60, npc="reverend")])


def _gym():
    rack = Rect(80, 120, 200, 130)
    return Room("gym", "Pump House Gym", (900, 600), "rubber", (200, 200, 205), (450, 520), [
        Furniture(rack, "gym"),
        F(600, 120, 220, 130, "gym"),
        F(120, 360, 90, 160, "treadmill"),
        F(260, 360, 90, 160, "treadmill"),
        F(700, 380, 140, 80, "bench"),
        F(360, 20, 180, 34, "mirrorwall", solid=False),
    ], [_spot("workout", rack, "Weights", 55), _spot("workout2", Rect(600, 120, 220, 130), "Weights", 55)])


ROOMS = {r.key: r for r in (
    _home(), _club(), _diner(), _office(), _pharmacy(), _clinic(), _studio(), _apartment(), _ballpark(), _hardware(),
    _shop("jeweler", "Rock Solid Jewelers", "tile", (40, 40, 52), "counter_glass", "Rock Solid Jewelers", "goldie",
          [(60, 300, 170, 70, "jewelcase"), (570, 300, 170, 70, "jewelcase"), (170, 18, 460, 60, "shelf_back")]),
    _shop("florist", "Petal Pushers", "wood", (235, 245, 230), "counter_green", "Petal Pushers", "fern",
          [(60, 290, 140, 140, "flowers"), (600, 290, 140, 140, "flowers"), (330, 330, 140, 100, "flowers")]),
    _shop("petshop", "Nuts & Eggs", "lino", (235, 240, 215), "counter_orange", "Nuts & Eggs pet shop", "tad",
          [(60, 280, 150, 120, "petcage"), (325, 300, 150, 110, "petcage"), (590, 280, 150, 120, "petcage")]),
    _shop("boutique", "Birthday Suits", "dark", (60, 40, 60), "counter_pink", "Birthday Suits boutique", "vee",
          [(60, 280, 60, 190, "rack"), (680, 280, 60, 190, "rack"), (340, 300, 120, 30, "mirrorwall")]),
    _chapel(), _gym())}
for _room in ROOMS.values():
    w, h = _room.size
    _room.hotspots.append(Hotspot("exit", Rect(w // 2 - 70, h - 60, 140, 60), "Exit"))
