"""Character art for Genitopia: soft-shaded cartoon mascots with no outlines.

Sprites are painted at 3x size and smooth-scaled down (cheap anti-aliasing), then cached,
so the detailed painting only happens once per look/pose.
"""
from __future__ import annotations

import math
import random

import pygame

from .model import BODY_COLORS, HAIR_COLORS, ONESIE_COLORS, Baby, Character

SS = 3                      # supersampling factor
CANVAS = (240, 350)         # sprite canvas in art units; feet sit near the bottom centre
FEET_Y = 338
_cache: dict = {}


# ---- colour helpers -----------------------------------------------------------
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, f):
    if f >= 1:
        return lerp(c, (255, 255, 255), min(1, f - 1))
    return tuple(int(v * f) for v in c)


def mix(a, b, t=0.5):
    return lerp(a, b, t)


class Pen:
    """Draws in art units (origin = feet) onto a supersampled surface."""

    def __init__(self, surf, k):
        self.s, self.k = surf, k
        self.ox, self.oy = surf.get_width() / 2, FEET_Y * k

    def p(self, x, y):
        return self.ox + x * self.k, self.oy + y * self.k

    def rect(self, cx, cy, w, h):
        x, y = self.p(cx - w / 2, cy - h / 2)
        return pygame.Rect(round(x), round(y), max(1, round(w * self.k)), max(1, round(h * self.k)))

    def ellipse(self, col, cx, cy, w, h):
        pygame.draw.ellipse(self.s, col, self.rect(cx, cy, w, h))

    def circle(self, col, cx, cy, r):
        self.ellipse(col, cx, cy, 2 * r, 2 * r)

    def rrect(self, col, cx, cy, w, h, r):
        pygame.draw.rect(self.s, col, self.rect(cx, cy, w, h), border_radius=round(r * self.k))

    def poly(self, col, pts):
        pygame.draw.polygon(self.s, col, [self.p(x, y) for x, y in pts])

    def alpha_ellipse(self, rgba, cx, cy, w, h):
        r = self.rect(cx, cy, w, h)
        tmp = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, rgba, tmp.get_rect())
        self.s.blit(tmp, r)

    def stroke(self, col, pts, width):
        pts = [self.p(x, y) for x, y in pts]
        w = max(1, round(width * self.k))
        pygame.draw.lines(self.s, col, False, pts, w)
        for x, y in (pts[0], pts[-1]):
            pygame.draw.circle(self.s, col, (x, y), w / 2)

    # soft 3D shapes: layered from a dark rim to a lit centre (light from the top-left)
    def blob(self, col, cx, cy, w, h, steps=18, dark=0.7, light=1.12, shift=0.22):
        for i in range(steps):
            t = i / (steps - 1)
            c = lerp(shade(col, dark), shade(col, light), t ** 0.75)
            f = 1 - 0.62 * t
            self.ellipse(c, cx - w * shift * t, cy - h * shift * t, w * f, h * f)
        self.alpha_ellipse((255, 255, 255, 55), cx - w * 0.22, cy - h * 0.26, w * 0.28, h * 0.18)

    def capsule(self, col, cx, cy, w, h, steps=16, dark=0.68, light=1.12):
        for i in range(steps):
            t = i / (steps - 1)
            c = lerp(shade(col, dark), shade(col, light), t ** 0.8)
            ww = w * (1 - 0.66 * t)
            hh = h * (1 - 0.1 * t)
            self.rrect(c, cx - w * 0.17 * t, cy - h * 0.02 * t, ww, hh, ww / 2)
        self.alpha_ellipse((255, 255, 255, 45), cx - w * 0.22, cy - h * 0.15, w * 0.16, h * 0.45)


# ---- body parts ---------------------------------------------------------------------
def _hair(pen, col, cx, cy, width, height, seed, density=1.0):
    rng = random.Random(seed)
    pen.ellipse(shade(col, 0.75), cx, cy + 2, width * 0.92, height * 0.8)
    n = int(width * height / 9 * density)
    for layer, f in ((0, 0.7), (1, 0.9), (2, 1.12)):
        for _ in range(n // 3):
            x = cx + rng.uniform(-width / 2, width / 2)
            edge = max(0.15, 1 - (2 * (x - cx) / width) ** 2)
            y = cy + rng.uniform(-height / 2, height / 2) * edge - layer * 2
            c = shade(col, f * rng.uniform(0.88, 1.12))
            r = rng.uniform(1.8, 3.4)
            pen.circle(c, x, y, r)
            if rng.random() < 0.35:  # little curl strands
                a = rng.uniform(0, math.tau)
                pen.stroke(c, [(x, y), (x + math.cos(a) * 5, y + math.sin(a) * 5)], 1.2)


def _leg_pose(frame, side):
    if frame < 0:
        return 0.0, 0.0
    ph = frame * math.pi / 2 + (0 if side < 0 else math.pi)
    return max(0.0, math.sin(ph)) * 9, math.cos(ph) * 4


def _legs(pen, skin, hip_x, hip_y, frame, shoe=(60, 60, 70)):
    for side in (-1, 1):
        lift, dx = _leg_pose(frame, side)
        x = side * hip_x + dx
        top, bottom = hip_y, -12 - lift
        pen.capsule(shade(skin, 0.9), x, (top + bottom) / 2, 17, bottom - top + 8, steps=8)
        pen.blob(shoe, x + side * 5, -10 - lift, 34, 16, steps=8, dark=0.6, light=1.4)
        pen.ellipse(shade(shoe, 1.6), x + side * 5, -4 - lift, 30, 4)


def _face(pen, skin, hair, fx, fy, mood, tired):
    for side in (-1, 1):
        ex = fx + side * 16
        pen.blob((250, 248, 245), ex, fy, 18, 21, steps=8, dark=0.82, light=1.0, shift=0.05)
        pen.circle((95, 62, 38), ex + 1.5, fy + 2, 6.5)
        pen.circle((60, 38, 24), ex + 1.5, fy + 2, 4.5)
        pen.circle((12, 10, 10), ex + 1.5, fy + 2, 3)
        pen.circle((255, 255, 255), ex - 1, fy - 1, 2)
        pen.circle((255, 255, 255), ex + 3.5, fy + 4.5, 0.9)
        if tired:
            pen.ellipse(shade(skin, 0.96), ex, fy - 8, 22, 18)
            pen.stroke(shade(skin, 0.5), [(ex - 9, fy + 1), (ex, fy + 2.5), (ex + 9, fy + 1)], 1.6)
        # eyebrows
        if mood >= 2:
            brow = [(ex - 8, fy - 14), (ex, fy - 17), (ex + 8, fy - 15)]
        elif mood == 1:
            brow = [(ex - 8, fy - 15), (ex + 8, fy - 15)]
        else:
            brow = [(ex - 8 * side, fy - 18), (ex + 8 * side, fy - 13)]
        pen.stroke(shade(hair, 1.05), brow, 2.6)
    for side in (-1, 1):
        pen.alpha_ellipse((240, 90, 110, 55), fx + side * 27, fy + 13, 14, 8)
    mx, my = fx, fy + 22
    lip = mix(shade(skin, 0.55), (120, 30, 40), 0.5)
    if mood >= 2:
        pen.ellipse(lip, mx, my, 26, 15)
        pen.ellipse((215, 110, 120), mx + 2, my + 4, 12, 6)
        pen.ellipse(shade(skin, 0.97), mx, my - 6, 30, 12)
    elif mood == 1:
        pen.rrect(lip, mx, my, 16, 3.5, 2)
    else:
        pen.ellipse(lip, mx, my + 2, 22, 12)
        pen.ellipse(shade(skin, 0.97), mx, my + 7, 26, 11)


def _ring(pen, x, y, skin):
    pen.circle((200, 205, 215), x, y, 5.5)
    pen.circle(shade(skin, 0.95), x, y - 1.2, 3.3)
    pen.circle((250, 250, 255), x - 2.5, y - 2.5, 1.1)


def _stud(pen, x, y):
    pen.circle((205, 210, 220), x, y, 3.2)
    pen.circle((255, 255, 255), x - 1, y - 1, 1.1)


def _accessory(pen, kind, top, hair):
    if kind == "tophat":
        pen.ellipse((25, 25, 30), 0, top + 2, 96, 16)
        pen.capsule((35, 35, 42), 0, top - 30, 58, 64, steps=6, dark=0.7, light=1.4)
        pen.rrect((150, 30, 40), 0, top - 8, 58, 9, 2)
    elif kind == "cap":
        pen.blob((40, 60, 120), 0, top - 6, 92, 50, steps=10)
        pen.ellipse((25, 35, 70), 14, top + 14, 70, 14)
        pen.blob((230, 190, 60), 0, top - 10, 14, 16, steps=5)
    elif kind == "chefhat":
        for x, y, r in ((-22, -24, 20), (0, -32, 24), (22, -24, 20)):
            pen.blob((250, 250, 250), x, top + y, r * 2, r * 2, steps=8, dark=0.85, light=1.0)
        pen.rrect((240, 240, 240), 0, top - 2, 70, 16, 4)
    elif kind == "hardhat":
        pen.blob((245, 200, 50), 0, top - 8, 96, 54, steps=10, light=1.25)
        pen.ellipse((215, 170, 35), 0, top + 12, 112, 14)
        pen.rrect((255, 225, 90), 0, top - 20, 10, 30, 4)
    elif kind == "headband":
        pen.rrect((240, 80, 130), 0, top + 18, 120, 14, 7)
        pen.rrect((255, 255, 255), 0, top + 18, 120, 3, 2)
    elif kind == "redcap":
        pen.blob((200, 45, 55), 0, top - 6, 92, 50, steps=10)
        pen.ellipse((160, 30, 40), 18, top + 14, 76, 14)
        pen.blob((250, 250, 250), 0, top - 10, 18, 16, steps=4)
    elif kind == "bow":
        for side in (-1, 1):
            pen.blob((240, 110, 160), side * 14, top, 26, 20, steps=6)
        pen.circle((220, 80, 130), 0, top, 6)


def _paint_character(look: Character, k, mood, tired, belly, frame, piercings):
    w, h = CANVAS
    surf = pygame.Surface((round(w * k), round(h * k)), pygame.SRCALPHA)
    pen = Pen(surf, k)
    skin = BODY_COLORS[look.body_color]
    hair = HAIR_COLORS[look.hair_color]
    seed = hash((look.kind, look.body_color, look.hair_color, look.name))
    pierce = set(piercings) | ({"Ear", "Eyebrow", "Lip", "Intimate"} if look.accessory == "studs" else set())

    if look.kind == "penis":
        _legs(pen, skin, 22, -64, frame)
        for side in (-1, 1):
            pen.blob(shade(skin, 0.92), side * 34, -84, 82, 76)
        _hair(pen, hair, 0, -110, 120, 26, seed)
        pen.capsule(skin, 0, -150, 76, 168)
        tip = mix(skin, (205, 110, 125), 0.28)
        pen.alpha_ellipse((0, 0, 0, 40), 0, -199, 80, 18)
        pen.blob(tip, 0, -228, 96, 78)
        pen.alpha_ellipse((255, 255, 255, 40), -6, -250, 40, 14)
        fx, fy = 0, -150
        _face(pen, skin, hair, fx, fy, mood, tired)
        spots = {"Ear": (-36, fy - 4), "Eyebrow": (28, fy - 17), "Lip": (12, fy + 30),
                 "Tongue": (0, fy + 26), "Intimate": (0, -264)}
        top = -266
    else:
        bw = 168 + belly * 14
        _legs(pen, skin, 30, -70, frame)
        pen.blob(skin, 0, -162, bw, 222)
        _hair(pen, hair, 0, -262, 118, 30, seed)
        if belly:
            bump_w, bump_h = 118 + belly * 22, 92 + belly * 18
            pen.blob(shade(skin, 1.03), 0, -118, bump_w, bump_h, steps=16, light=1.22)
            pen.circle(shade(skin, 0.75), 0, -112, 2.6)
            lab_cy, lab_w, lab_h = -58 - belly * 2, 26, 34
        else:
            lab_cy, lab_w, lab_h = -112, 46, 112
        pink = mix(skin, (205, 90, 120), 0.62)
        pen.blob(pink, 0, lab_cy, lab_w, lab_h, steps=12, dark=0.8, light=1.15, shift=0.1)
        pen.ellipse(shade(pink, 0.62), 0, lab_cy + lab_h * 0.05, lab_w * 0.22, lab_h * 0.78)
        pen.alpha_ellipse((255, 255, 255, 50), -lab_w * 0.18, lab_cy - lab_h * 0.25, lab_w * 0.2, lab_h * 0.3)
        fx, fy = 0, -210
        _face(pen, skin, hair, fx, fy, mood, tired)
        spots = {"Ear": (-bw / 2 + 12, fy + 4), "Eyebrow": (28, fy - 17), "Lip": (12, fy + 30),
                 "Tongue": (0, fy + 26), "Intimate": (0, lab_cy - lab_h / 2 + 2)}
        top = -272

    for name in pierce:
        x, y = spots[name]
        if name in ("Ear", "Tongue"):
            _stud(pen, x, y)
        else:
            _ring(pen, x, y, skin)
    if look.accessory == "glasses":
        for side in (-1, 1):
            c = pen.p(fx + side * 16, fy + 1)
            pygame.draw.circle(surf, (40, 40, 45), c, 14 * k, max(1, round(2 * k)))
        pen.stroke((40, 40, 45), [(fx - 3, fy), (fx + 3, fy)], 2)
    elif look.accessory:
        _accessory(pen, look.accessory, top, hair)
    return surf


def _scaled(key, painter, scale):
    surf = _cache.get(key)
    if surf is None:
        big = painter(scale * SS)
        size = (max(1, round(big.get_width() / SS)), max(1, round(big.get_height() / SS)))
        surf = pygame.transform.smoothscale(big, size)
        if len(_cache) > 400:
            _cache.clear()
        _cache[key] = surf
    return surf


def _mood_bucket(mood):
    return 2 if mood >= 60 else 1 if mood >= 30 else 0


def draw_shadow(surf, feet, w):
    x, y = feet
    tmp = pygame.Surface((int(w), int(w * 0.3)), pygame.SRCALPHA)
    pygame.draw.ellipse(tmp, (0, 0, 0, 70), tmp.get_rect())
    surf.blit(tmp, (x - w / 2, y - w * 0.15))


def draw_character(surf, look: Character, feet, scale=1.0, mood=70, energy=80, hygiene=80,
                   infected=False, ticks=0, piercings=(), belly=0, frame=-1, shadow=True, bob=True):
    """Draw a mascot standing with its feet at `feet`. frame: -1 idle, 0-3 walk cycle."""
    scale = round(scale, 2)
    mb, tired = _mood_bucket(mood), energy < 25
    key = ("c", look.kind, look.body_color, look.hair_color, look.accessory, look.name,
           scale, mb, tired, belly, frame, tuple(sorted(piercings)))
    sprite = _scaled(key, lambda k: _paint_character(look, k, mb, tired, belly, frame, piercings), scale)
    x, y = feet
    if shadow:
        draw_shadow(surf, feet, 120 * scale)
    lift = math.sin(ticks / 380) * 2.5 * scale if bob and frame < 0 else 0
    surf.blit(sprite, (x - sprite.get_width() / 2, y - FEET_Y * scale + lift))
    top = y - 280 * scale
    if hygiene < 30:
        for i, dx in enumerate((-40, 0, 40)):
            pts = [(x + dx * scale + math.sin(j * 1.2 + ticks / 200 + i) * 6 * scale,
                    top - 8 * scale - j * 6 * scale) for j in range(8)]
            pygame.draw.lines(surf, (130, 175, 70), False, pts, max(2, int(3 * scale)))
    if infected:
        for ang in (0.6, 2.2, 3.9, 5.1):
            pygame.draw.circle(surf, (215, 50, 50),
                               (x + math.cos(ang) * 30 * scale, y - 150 * scale + math.sin(ang) * 30 * scale),
                               max(2, 5 * scale))


# ---- baby -----------------------------------------------------------------------------
def _paint_baby(b: Baby, k, crying, frame):
    w, h = CANVAS
    surf = pygame.Surface((round(w * k), round(h * k)), pygame.SRCALPHA)
    pen = Pen(surf, k)
    skin = BODY_COLORS[b.skin]
    hair = HAIR_COLORS[b.hair]
    cloth = ONESIE_COLORS[b.onesie]
    for side in (-1, 1):
        lift, dx = _leg_pose(frame, side)
        pen.capsule(cloth, side * 12 + dx, -16 - lift / 2, 16, 26, steps=6)
        pen.blob(shade(skin, 1.0), side * 13 + dx, -6 - lift, 16, 11, steps=5)
    pen.blob(cloth, 0, -40, 50, 46)
    pen.circle(shade(cloth, 1.25), -4, -44, 3)          # little snap buttons
    pen.circle(shade(cloth, 1.25), -4, -34, 3)
    for side in (-1, 1):
        pen.blob(skin, side * 26, -44, 14, 14, steps=5)
    pen.blob(skin, 0, -84, 60, 56)
    rng = random.Random(hash((b.hair, b.name)))
    for _ in range(9):
        pen.circle(shade(hair, rng.uniform(0.85, 1.2)), rng.uniform(-8, 8), -110 + rng.uniform(-3, 3),
                   rng.uniform(2.5, 4.5))
    for side in (-1, 1):
        ex = side * 11
        pen.ellipse((25, 20, 20), ex, -86, 9, 11)
        pen.circle((255, 255, 255), ex - 1.5, -89, 1.8)
        pen.alpha_ellipse((245, 110, 130, 70), side * 19, -76, 11, 7)
        if crying:
            pen.blob((120, 190, 245), ex + side * 4, -74, 5, 8, steps=3)
    if crying:
        pen.ellipse((120, 40, 50), 0, -68, 12, 9)
    else:
        pen.ellipse((120, 40, 50), 0, -71, 12, 7)
        pen.ellipse(shade(skin, 1.0), 0, -74, 14, 6)
    if b.accessory == "Bow":
        for side in (-1, 1):
            pen.blob((240, 110, 160), side * 9 + 14, -110, 14, 11, steps=5)
        pen.circle((215, 80, 130), 14, -110, 3.5)
    elif b.accessory == "Beanie":
        pen.blob(cloth, 0, -102, 62, 34, steps=8)
        pen.rrect(shade(cloth, 0.85), 0, -92, 62, 9, 4)
        pen.blob((250, 250, 250), 0, -122, 14, 14, steps=5)
    elif b.accessory == "Pacifier" and not crying:
        pen.blob((120, 200, 230), 0, -70, 18, 12, steps=5)
        pen.circle((240, 240, 250), 0, -70, 3.5)
    return surf


def draw_baby(surf, b: Baby, feet, scale=1.0, ticks=0, frame=-1):
    scale = round(scale, 2)
    key = ("b", b.skin, b.hair, b.onesie, b.accessory, b.name, b.crying, frame, scale)
    sprite = _scaled(key, lambda k: _paint_baby(b, k, b.crying, frame), scale)
    draw_shadow(surf, feet, 60 * scale)
    x, y = feet
    hop = abs(math.sin(ticks / 160)) * 3 * scale if frame >= 0 else 0
    surf.blit(sprite, (x - sprite.get_width() / 2, y - FEET_Y * scale - hop))
