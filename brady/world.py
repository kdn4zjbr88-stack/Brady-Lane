"""Map data: the walkable town and each building's interior."""
from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Rect


@dataclass
class Furniture:
    rect: Rect
    color: tuple
    label: str = ""
    solid: bool = True


@dataclass
class Hotspot:
    key: str          # what the interaction is, e.g. "shower" or "door:club"
    zone: Rect        # standing inside this triggers the pop-up
    title: str


@dataclass
class Building:
    key: str
    name: str
    rect: Rect
    color: tuple
    roof: tuple
    door_side: str    # "bottom" or "top"

    @property
    def door(self) -> Rect:
        d = Rect(0, 0, 70, 16)
        if self.door_side == "bottom":
            d.midbottom = self.rect.midbottom
        else:
            d.midtop = self.rect.midtop
        return d

    @property
    def door_zone(self) -> Rect:
        z = Rect(0, 0, 110, 80)
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
    floor: tuple
    spawn: tuple[int, int]
    furniture: list[Furniture] = field(default_factory=list)
    hotspots: list[Hotspot] = field(default_factory=list)

    def solids(self) -> list[Rect]:
        return [f.rect for f in self.furniture if f.solid]


def _spot(key, rect, title, pad=55):
    return Hotspot(key, rect.inflate(pad * 2, pad * 2), title)


# ---- town -------------------------------------------------------------------
TOWN_SIZE = (2600, 1700)
ROADS = [Rect(0, 760, 2600, 120), Rect(1240, 0, 120, 1700)]

BUILDINGS = [
    Building("home", "Home", Rect(200, 300, 360, 320), (150, 120, 95), (110, 60, 50), "bottom"),
    Building("diner", "Diner", Rect(700, 380, 300, 240), (210, 200, 170), (200, 60, 60), "bottom"),
    Building("office", "Office", Rect(1500, 260, 380, 360), (130, 140, 160), (70, 80, 100), "bottom"),
    Building("pharmacy", "Pharmacy", Rect(2020, 380, 300, 240), (230, 235, 235), (40, 160, 90), "bottom"),
    Building("club", "Club Velvet", Rect(200, 1000, 440, 340), (60, 30, 70), (150, 40, 120), "top"),
    Building("studio", "Ink & Steel", Rect(760, 1000, 300, 260), (70, 70, 75), (30, 30, 30), "top"),
    Building("clinic", "Clinic", Rect(1500, 1000, 340, 300), (235, 240, 245), (60, 120, 200), "top"),
    Building("apartments", "Apartments", Rect(1980, 1000, 420, 400), (170, 110, 90), (90, 60, 50), "top"),
]
BUILDING_BY_KEY = {b.key: b for b in BUILDINGS}

TREES = [(120, 120), (640, 160), (1120, 220), (1980, 140), (2480, 260), (120, 700), (1140, 640),
         (2480, 680), (120, 1500), (700, 1460), (1180, 1100), (1420, 1520), (1900, 1560),
         (2520, 1560), (1120, 1560), (980, 120)]

# ---- interiors --------------------------------------------------------------
WOOD, TILE, CARPET, DARK = (120, 90, 65), (200, 205, 210), (110, 70, 90), (35, 25, 45)


def _home():
    bed = Rect(60, 60, 220, 150)
    mirror = Rect(330, 26, 90, 16)
    fridge = Rect(60, 460, 90, 130)
    shower = Rect(800, 40, 160, 150)
    toilet = Rect(880, 270, 70, 70)
    return Room("home", "Home", (1000, 640), WOOD, (500, 560), [
        Furniture(bed, (90, 120, 200), "Bed"),
        Furniture(mirror, (190, 220, 240), "Mirror"),
        Furniture(fridge, (230, 230, 235), "Fridge"),
        Furniture(Rect(640, 0, 20, 240), (80, 60, 45)),
        Furniture(Rect(640, 340, 20, 300), (80, 60, 45)),
        Furniture(Rect(660, 0, 340, 640), TILE, solid=False),
        Furniture(shower, (150, 200, 230), "Shower"),
        Furniture(toilet, (245, 245, 245), "Toilet"),
        Furniture(Rect(300, 300, 200, 110), (150, 70, 60), "Couch"),
    ], [
        _spot("sleep", bed, "Your bed"),
        _spot("mirror", mirror, "Mirror", 45),
        _spot("snack", fridge, "Fridge"),
        _spot("shower", shower, "Bathroom: shower"),
        _spot("pee", toilet, "Bathroom: toilet", 40),
    ])


def _club():
    floor = Rect(380, 180, 460, 360)
    bar = Rect(40, 80, 70, 520)
    return Room("club", "Club Velvet", (1200, 760), DARK, (600, 680), [
        Furniture(floor, (120, 40, 140), "Dance floor", solid=False),
        Furniture(bar, (120, 70, 40), "Bar"),
        Furniture(Rect(500, 40, 220, 70), (40, 40, 40), "DJ"),
        Furniture(Rect(1000, 120, 160, 90), (90, 30, 60), "VIP"),
        Furniture(Rect(1000, 500, 160, 90), (90, 30, 60), "VIP"),
    ], [
        Hotspot("dance", floor, "Dance floor"),
        _spot("bar", bar, "Bar", 60),
    ])


def _simple(key, name, size, floor, counter, color, label, spot_key, spot_title, extras=()):
    w, h = size
    return Room(key, name, size, floor, (w // 2, h - 110),
                [Furniture(counter, color, label), *extras],
                [_spot(spot_key, counter, spot_title)])


def _apartment():
    bed = Rect(580, 80, 260, 180)
    return Room("apartments", "Their bedroom", (900, 600), CARPET, (450, 520), [
        Furniture(bed, (200, 60, 80), "Bed"),
        Furniture(Rect(60, 60, 140, 60), (90, 60, 45), "Dresser"),
        Furniture(Rect(60, 380, 160, 120), (60, 50, 70), "Couch"),
    ], [_spot("bed", bed, "Their bed", 70)])


ROOMS = {
    "home": _home(),
    "club": _club(),
    "diner": _simple("diner", "Diner", (900, 600), (230, 220, 200), Rect(100, 120, 700, 60),
                     (180, 50, 50), "Counter", "eat", "Order at the counter",
                     [Furniture(Rect(150, 330, 120, 80), (200, 60, 60)),
                      Furniture(Rect(630, 330, 120, 80), (200, 60, 60))]),
    "office": _simple("office", "Office", (900, 600), (170, 175, 185), Rect(370, 200, 160, 80),
                      (110, 85, 60), "Your desk", "work", "Your desk",
                      [Furniture(Rect(80, 80, 140, 70), (110, 85, 60)),
                       Furniture(Rect(680, 80, 140, 70), (110, 85, 60))]),
    "pharmacy": _simple("pharmacy", "Pharmacy", (800, 560), (235, 240, 240), Rect(150, 110, 500, 60),
                        (40, 160, 90), "Pharmacist", "pharmacy", "Pharmacy counter"),
    "clinic": _simple("clinic", "Clinic", (800, 560), (225, 235, 245), Rect(300, 130, 200, 70),
                      (60, 120, 200), "Doctor", "clinic", "Doctor"),
    "studio": _simple("studio", "Ink & Steel", (800, 560), (50, 50, 55), Rect(350, 170, 100, 110),
                      (150, 30, 40), "Chair", "studio", "Piercing chair"),
    "apartments": _apartment(),
}
for room in ROOMS.values():
    w, h = room.size
    room.hotspots.append(Hotspot("exit", Rect(w // 2 - 70, h - 60, 140, 60), "Exit"))
