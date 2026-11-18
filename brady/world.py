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


@dataclass
class Hotspot:
    key: str          # what the interaction is, e.g. "shower" or "door:club"
    zone: Rect        # standing inside this triggers the pop-up
    title: str
    npc: str = ""     # shopkeeper attached to this spot (adds a "Chat" option)


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

    def solids(self) -> list[Rect]:
        return [f.rect for f in self.furniture if f.solid]


def _spot(key, rect, title, pad=55, npc=""):
    return Hotspot(key, rect.inflate(pad * 2, pad * 2), title, npc)


# ---- town -------------------------------------------------------------------
TOWN_SIZE = (2600, 1700)
ROADS = [Rect(0, 760, 2600, 120), Rect(1240, 0, 120, 1700)]
SIDEWALKS = [Rect(0, 732, 2600, 28), Rect(0, 880, 2600, 28), Rect(1212, 0, 28, 1700), Rect(1360, 0, 28, 1700)]

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
]
BUILDING_BY_KEY = {b.key: b for b in BUILDINGS}

TREES = [(120, 120), (640, 160), (1120, 220), (1980, 140), (2480, 260), (1140, 620), (2480, 640),
         (120, 1500), (700, 1460), (1150, 1120), (1420, 1560), (1920, 1580), (2520, 1580),
         (1110, 1600), (980, 120), (2440, 1250)]
FOUNTAIN = (1660, 1500, 70)       # x, y, radius
BENCHES = [(1560, 1430), (1760, 1430), (640, 922)]
LAMPS = [(x, 730) for x in range(160, 2600, 320)] + [(x, 910) for x in range(320, 2600, 320)]
FLOWERBEDS = [Rect(220, 630, 90, 22), Rect(450, 630, 90, 22), Rect(2040, 630, 80, 22),
              Rect(2220, 630, 80, 22), Rect(1520, 972, 90, 22), Rect(1730, 972, 90, 22)]
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
    bed, crib, mirror = Rect(60, 70, 220, 150), Rect(310, 70, 100, 80), Rect(450, 6, 80, 40)
    fridge, shower, toilet = Rect(60, 470, 90, 130), Rect(800, 40, 160, 150), Rect(880, 280, 70, 70)
    return Room("home", "Home", (1000, 640), "wood", (215, 200, 180), (500, 560), [
        F(660, 0, 340, 640, "tilefloor", solid=False),
        F(320, 280, 260, 160, "rug", solid=False),
        Furniture(bed, "bed"),
        Furniture(crib, "crib"),
        Furniture(mirror, "mirror", solid=False),
        Furniture(fridge, "fridge"),
        F(150, 520, 150, 80, "kitchen"),
        F(340, 440, 210, 90, "couch"),
        F(640, 0, 20, 240, "wall"),
        F(640, 340, 20, 300, "wall"),
        Furniture(shower, "shower"),
        Furniture(toilet, "toilet"),
        F(700, 30, 70, 50, "sink"),
        F(580, 560, 44, 44, "plant"),
    ], [
        _spot("sleep", bed, "Your bed"),
        _spot("crib", crib, "Crib", 45),
        _spot("mirror", Rect(450, 30, 80, 20), "Mirror", 40),
        _spot("snack", fridge, "Fridge"),
        _spot("shower", shower, "Bathroom: shower"),
        _spot("pee", toilet, "Bathroom: toilet", 40),
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


ROOMS = {r.key: r for r in (_home(), _club(), _diner(), _office(), _pharmacy(), _clinic(), _studio(), _apartment())}
for _room in ROOMS.values():
    w, h = _room.size
    _room.hotspots.append(Hotspot("exit", Rect(w // 2 - 70, h - 60, 140, 60), "Exit"))
