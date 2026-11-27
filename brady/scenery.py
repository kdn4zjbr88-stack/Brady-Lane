"""Paints Genitopia's town and interiors: soft gradients, textures and shadows, no outlines.

Static backgrounds are painted once and cached; only lights, rain and animated bits are live.
"""
from __future__ import annotations

import math
import random

import pygame

from .art import draw_character, lerp, shade
from .model import Character
from .world import (BENCHES, BUILDINGS, FLOWERBEDS, FOUNTAIN, LAMPS, ROADS, ROOMS, SIDEWALKS, TOWN_SIZE,
                    TREES, WELCOME_SIGN, Building, Room)

_cache: dict = {}
_font_cache: dict = {}


def font(size, bold=True):
    f = _font_cache.get((size, bold))
    if f is None:
        f = pygame.font.SysFont("arial,helvetica,dejavusans", size, bold=bold)
        _font_cache[(size, bold)] = f
    return f


# ---- primitives ------------------------------------------------------------------
def grad_surface(size, top, bottom, radius=0, horizontal=False):
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    n = w if horizontal else h
    for i in range(n):
        c = lerp(top, bottom, i / max(1, n - 1))
        if horizontal:
            pygame.draw.line(s, c, (i, 0), (i, h))
        else:
            pygame.draw.line(s, c, (0, i), (w, i))
    if radius:
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=int(radius))
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return s


def grad(surf, rect, top, bottom, radius=0, horizontal=False):
    rect = pygame.Rect(rect)
    surf.blit(grad_surface(rect.size, top, bottom, radius, horizontal), rect.topleft)


def soft_shadow(surf, rect, offset=(8, 10), alpha=60, radius=10, blur=3):
    rect = pygame.Rect(rect).move(offset)
    for i in range(blur, 0, -1):
        tmp = pygame.Surface(rect.inflate(i * 6, i * 6).size, pygame.SRCALPHA)
        pygame.draw.rect(tmp, (0, 0, 0, alpha // (blur + 1)), tmp.get_rect(), border_radius=radius + i * 3)
        surf.blit(tmp, rect.inflate(i * 6, i * 6).topleft)


def alpha_ellipse(surf, rgba, rect):
    rect = pygame.Rect(rect)
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(tmp, rgba, tmp.get_rect())
    surf.blit(tmp, rect.topleft)


def alpha_rect(surf, rgba, rect, radius=0):
    rect = pygame.Rect(rect)
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(tmp, rgba, tmp.get_rect(), border_radius=radius)
    surf.blit(tmp, rect.topleft)


def ball(surf, col, center, r, light=1.25, dark=0.7, steps=10):
    x, y = center
    for i in range(steps):
        t = i / (steps - 1)
        rr = r * (1 - 0.6 * t)
        pygame.draw.circle(surf, lerp(shade(col, dark), shade(col, light), t),
                           (x - r * 0.25 * t, y - r * 0.25 * t), rr)


def noise(surf, rect, base, amount, count, rng, size=(1, 3)):
    rect = pygame.Rect(rect)
    for _ in range(count):
        f = 1 + rng.uniform(-amount, amount)
        x, y = rng.randint(rect.left, rect.right - 1), rng.randint(rect.top, rect.bottom - 1)
        r = rng.uniform(*size)
        pygame.draw.circle(surf, shade(base, f), (x, y), r)


# ---- town ------------------------------------------------------------------------
GRASS = (92, 145, 78)
ASPHALT = (68, 68, 76)
PAVEMENT = (190, 186, 178)


def _tree(s, x, y, rng):
    alpha_ellipse(s, (0, 0, 0, 55), (x - 34, y - 6, 80, 26))
    pygame.draw.rect(s, (95, 65, 45), (x - 7, y - 30, 14, 34), border_radius=5)
    for i in range(14):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 26)
        ball(s, (60 + rng.randint(-8, 8), 118 + rng.randint(-12, 12), 58), (x + math.cos(a) * d, y - 58 + math.sin(a) * d * 0.8),
             rng.uniform(16, 24), light=1.3, dark=0.75, steps=7)


def _bench(s, x, y):
    alpha_rect(s, (0, 0, 0, 50), (x - 36, y + 2, 76, 10), 5)
    grad(s, (x - 38, y - 18, 76, 10), (170, 120, 80), (130, 90, 60), 3)
    grad(s, (x - 38, y - 6, 76, 10), (160, 112, 74), (120, 82, 54), 3)
    for dx in (-30, 26):
        pygame.draw.rect(s, (60, 60, 66), (x + dx, y + 2, 5, 8))


def _flowers(s, rect, rng):
    grad(s, rect, (110, 80, 55), (85, 60, 40), 8)
    for _ in range(rect.w // 5):
        cx, cy = rng.randint(rect.left + 4, rect.right - 4), rng.randint(rect.top + 3, rect.bottom - 3)
        pygame.draw.circle(s, (60, 120, 55), (cx, cy + 2), 3)
        ball(s, rng.choice([(235, 90, 130), (250, 210, 80), (170, 120, 230), (250, 250, 250)]), (cx, cy), 3, steps=3)


def _fountain(s):
    x, y, r = FOUNTAIN
    pygame.draw.circle(s, (176, 170, 160), (x, y), r + 50)
    noise(s, (x - r - 45, y - r - 45, 2 * r + 90, 2 * r + 90), (176, 170, 160), 0.06, 900, random.Random(4))
    alpha_ellipse(s, (0, 0, 0, 60), (x - r - 4, y - r * 0.6 + 8, 2 * r + 16, r * 1.3))
    pygame.draw.ellipse(s, (205, 200, 192), (x - r, y - r * 0.62, 2 * r, r * 1.24))
    grad(s, (x - r + 10, y - r * 0.5, 2 * r - 20, r), (90, 160, 210), (60, 120, 180), int(r * 0.5))
    pygame.draw.ellipse(s, (205, 200, 192), (x - 14, y - 34, 28, 40))
    t = font(16).render("GENITOPIA SQUARE", True, (90, 85, 80))
    s.blit(t, t.get_rect(center=(x, y + r + 32)))


def _sign(s):
    r = WELCOME_SIGN
    for px in (r.x + 22, r.right - 26):
        pygame.draw.rect(s, (110, 80, 55), (px, r.y + 30, 8, r.h - 22))
    soft_shadow(s, (r.x, r.y, r.w, 46), (5, 6), 70, 8)
    grad(s, (r.x, r.y, r.w, 46), (90, 160, 110), (55, 120, 80), 8)
    t1 = font(12).render("WELCOME TO", True, (235, 245, 235))
    t2 = font(20).render("GENITOPIA", True, (255, 255, 255))
    s.blit(t1, t1.get_rect(center=(r.centerx, r.y + 12)))
    s.blit(t2, t2.get_rect(center=(r.centerx, r.y + 30)))


def _layout(b: Building):
    """Split a building into (roof, facade) rects; the facade faces the road the door is on."""
    r = b.rect
    roof_h = int(r.h * 0.34)
    if b.door_side == "bottom":
        return pygame.Rect(r.x, r.y, r.w, roof_h), pygame.Rect(r.x, r.y + roof_h, r.w, r.h - roof_h)
    return pygame.Rect(r.x, r.bottom - roof_h, r.w, roof_h), pygame.Rect(r.x, r.y, r.w, r.h - roof_h)


def _door_rect(b: Building):
    roof, face = _layout(b)
    if b.door_side == "bottom":
        return pygame.Rect(face.centerx - 32, face.bottom - 72, 64, 72)
    return pygame.Rect(face.centerx - 32, face.y + 30, 64, 72)


def window_rects(b: Building):
    if b.key == "ballpark":
        return []
    roof, face = _layout(b)
    door = _door_rect(b).inflate(70, 30)
    out = []
    for wx in range(face.left + 26, face.right - 50, 72):
        for wy in range(face.top + 22, face.bottom - 50, 78):
            w = pygame.Rect(wx, wy, 36, 40)
            if not w.colliderect(door):
                out.append(w)
    return out


def _stadium(s, b: Building):
    r = b.rect
    soft_shadow(s, r, (14, 16), 90, 120, 3)
    pygame.draw.ellipse(s, (150, 148, 145), r)
    for i, c in enumerate([(70, 110, 170), (60, 95, 150), (80, 125, 185), (60, 95, 150)]):
        pygame.draw.ellipse(s, c, r.inflate(-30 - i * 34, -26 - i * 30))
        rng = random.Random(i)
        inner = r.inflate(-30 - i * 34, -26 - i * 30)
        for _ in range(220):                      # fans in the stands
            a = rng.uniform(0, math.tau)
            px = inner.centerx + math.cos(a) * (inner.w / 2 - 8)
            py = inner.centery + math.sin(a) * (inner.h / 2 - 8)
            pygame.draw.circle(s, rng.choice([(240, 200, 160), (120, 80, 50), (200, 60, 80), (250, 250, 250)]),
                               (px, py), 3)
    field = r.inflate(-190, -170)
    pygame.draw.ellipse(s, (70, 140, 70), field)
    for i in range(0, field.w, 26):
        alpha_rect(s, (255, 255, 255, 12) if (i // 26) % 2 else (0, 0, 0, 8), (field.x + i, field.y + 20, 13, field.h - 40))
    cx, cy = field.centerx, field.centery + 30
    diamond = [(cx, cy + 70), (cx + 70, cy), (cx, cy - 70), (cx - 70, cy)]
    pygame.draw.polygon(s, (190, 140, 90), [(x, y + 6) for x, y in diamond])
    pygame.draw.polygon(s, (70, 140, 70), [(cx, cy + 46), (cx + 44, cy + 2), (cx, cy - 42), (cx - 44, cy + 2)])
    for x, y in diamond:
        pygame.draw.rect(s, (250, 250, 250), (x - 5, y + 1, 10, 10))
    pygame.draw.circle(s, (190, 140, 90), (cx, cy + 4), 12)
    gate = pygame.Rect(r.centerx - 90, r.y - 4, 180, 56)
    soft_shadow(s, gate, (4, 6), 70, 8, 2)
    grad(s, gate, (40, 90, 160), (25, 60, 115), 10)
    t = font(18).render("BALLERS STADIUM", True, (255, 255, 255))
    s.blit(t, t.get_rect(center=(gate.centerx, gate.y + 20)))
    t2 = font(11, False).render("Home of the Genitopia Ballers", True, (220, 230, 245))
    s.blit(t2, t2.get_rect(center=(gate.centerx, gate.y + 40)))
    for fx_, fy_ in ((r.x + 60, r.y + 60), (r.right - 60, r.y + 60), (r.x + 60, r.bottom - 60), (r.right - 60, r.bottom - 60)):
        pygame.draw.rect(s, (70, 70, 78), (fx_ - 3, fy_ - 4, 6, 40))
        grad(s, (fx_ - 18, fy_ - 18, 36, 16), (240, 240, 235), (190, 190, 185), 4)


STADIUM_LIGHTS = []


def _building(s, b: Building):
    if b.key == "ballpark":
        return _stadium(s, b)
    r = b.rect
    soft_shadow(s, r, (12, 14), 80, 8)
    roof_r, face = _layout(b)
    light_wall = sum(b.wall) > 600
    grad(s, face, shade(b.wall, 1.04), shade(b.wall, 0.84))
    rng = random.Random(b.key)
    for y in range(face.top + 6, face.bottom, 9):            # siding texture
        alpha_rect(s, (0, 0, 0, 10 if light_wall else 14), (face.x, y, face.w, 1))
    if not light_wall:
        noise(s, face, shade(b.wall, 0.95), 0.04, face.w * face.h // 60, rng)
    roof = roof_r.inflate(12, 6)
    if b.door_side == "bottom":
        grad(s, roof, shade(b.roof, 1.18), shade(b.roof, 0.72), 6)
        alpha_rect(s, (0, 0, 0, 60), (face.x, face.y, face.w, 8))
    else:
        grad(s, roof, shade(b.roof, 0.95), shade(b.roof, 0.65), 6)
        alpha_rect(s, (255, 255, 255, 30), (face.x, face.y, face.w, 6))
        alpha_rect(s, (0, 0, 0, 70), (face.x, face.bottom - 6, face.w, 6))
    for y in range(roof.top + 8, roof.bottom - 6, 10):         # roof tiles
        alpha_rect(s, (0, 0, 0, 28), (roof.x + 4, y, roof.w - 8, 2))
    alpha_rect(s, (255, 255, 255, 40), (roof.x + 4, roof.y + 3, roof.w - 8, 4), 2)
    for w in window_rects(b):
        pygame.draw.rect(s, shade(b.wall, 1.2), w.inflate(8, 8), border_radius=3)
        grad(s, w, (170, 205, 230), (95, 130, 165), 2)
        pygame.draw.polygon(s, (205, 228, 245), [(w.x + 6, w.bottom - 4), (w.x + 18, w.y + 4),
                                                 (w.x + 24, w.y + 4), (w.x + 12, w.bottom - 4)])
        pygame.draw.rect(s, shade(b.wall, 1.2), (w.centerx - 1, w.y, 3, w.h))
        alpha_rect(s, (0, 0, 0, 50), (w.x - 4, w.bottom + 4, w.w + 8, 4), 2)
    d = _door_rect(b)
    pygame.draw.rect(s, shade(b.wall, 0.6), d.inflate(10, 6).move(0, -3), border_radius=6)
    grad(s, d, (120, 80, 55), (80, 52, 36), 4)
    pygame.draw.circle(s, (225, 195, 90), (d.right - 12, d.centery), 4)
    if b.awning:
        aw = pygame.Rect(d.x - 26, d.y - 26, d.w + 52, 22)
        for i in range(0, aw.w, 14):
            col = b.awning if (i // 14) % 2 == 0 else (245, 240, 235)
            grad(s, (aw.x + i, aw.y, 14, aw.h), shade(col, 1.1), shade(col, 0.8))
        alpha_rect(s, (0, 0, 0, 60), (aw.x, aw.bottom, aw.w, 6))
    sign = pygame.Rect(0, 0, min(r.w - 30, 30 + len(b.name) * 13), 30)
    sign.center = roof_r.center
    soft_shadow(s, sign, (3, 4), 70, 8, 2)
    grad(s, sign, (45, 40, 50), (25, 22, 30), 8)
    t = font(18).render(b.name, True, (250, 245, 235))
    s.blit(t, t.get_rect(center=sign.center))


def town_surface():
    if "town" in _cache:
        return _cache["town"]
    w, h = TOWN_SIZE
    s = pygame.Surface((w, h))
    rng = random.Random(7)
    s.fill(GRASS)
    for _ in range(9000):                        # grass texture
        x, y = rng.randint(0, w), rng.randint(0, h)
        c = shade(GRASS, rng.uniform(0.82, 1.16))
        pygame.draw.line(s, c, (x, y), (x + rng.randint(-2, 2), y - rng.randint(3, 7)), 2)
    for _ in range(60):                          # soft light patches
        alpha_ellipse(s, (255, 255, 200, 14), (rng.randint(0, w), rng.randint(0, h), 240, 140))
    for sw in SIDEWALKS:
        pygame.draw.rect(s, PAVEMENT, sw)
        noise(s, sw, PAVEMENT, 0.05, sw.w * sw.h // 40, rng, (0.6, 1.6))
        step = 40
        if sw.w > sw.h:
            for x in range(sw.x, sw.right, step):
                pygame.draw.line(s, shade(PAVEMENT, 0.85), (x, sw.y), (x, sw.bottom))
        else:
            for y in range(sw.y, sw.bottom, step):
                pygame.draw.line(s, shade(PAVEMENT, 0.85), (sw.x, y), (sw.right, y))
    for r in ROADS:
        pygame.draw.rect(s, ASPHALT, r)
        noise(s, r, ASPHALT, 0.12, r.w * r.h // 30, rng, (0.5, 1.4))
    horiz = [r for r in ROADS if r.w > r.h]
    vert = [r for r in ROADS if r.h > r.w]
    for r in horiz:                              # lane markings
        for x in range(0, w, 80):
            if not any(v.left - 10 < x < v.right + 10 for v in vert):
                pygame.draw.rect(s, (230, 205, 100), (x, r.centery - 3, 42, 6), border_radius=3)
    for v in vert:
        for y in range(0, h, 80):
            if not any(r.top - 10 < y < r.bottom + 10 for r in horiz):
                pygame.draw.rect(s, (230, 205, 100), (v.centerx - 3, y, 6, 42), border_radius=3)
        for r in horiz:                          # crosswalks at each intersection
            for i in range(7):
                pygame.draw.rect(s, (235, 235, 235), (v.left - 70, r.top + 10 + i * 16, 50, 9), border_radius=2)
                pygame.draw.rect(s, (235, 235, 235), (v.right + 20, r.top + 10 + i * 16, 50, 9), border_radius=2)
                pygame.draw.rect(s, (235, 235, 235), (v.left + 10 + i * 16, r.top - 70, 9, 50), border_radius=2)
                pygame.draw.rect(s, (235, 235, 235), (v.left + 10 + i * 16, r.bottom + 10, 9, 50), border_radius=2)
    for b in BUILDINGS:                          # driveway/path to each door
        dz = b.door_zone
        pygame.draw.rect(s, PAVEMENT, dz.inflate(-30, 0), border_radius=6)
    _fountain(s)
    for fb in FLOWERBEDS:
        _flowers(s, fb, rng)
    for b in BUILDINGS:
        _building(s, b)
    for x, y in BENCHES:
        _bench(s, x, y)
    _sign(s)
    for x, y in LAMPS:
        alpha_ellipse(s, (0, 0, 0, 50), (x - 10, y - 3, 22, 8))
        pygame.draw.rect(s, (55, 55, 62), (x - 3, y - 70, 6, 72), border_radius=3)
        ball(s, (240, 235, 210), (x, y - 74), 8, steps=5)
    for x, y in TREES:
        _tree(s, x, y, random.Random(x * 7 + y))
    _cache["town"] = s
    return s


def town_occluders():
    """(sort_y, rect) pieces of the background that should cover characters standing behind them."""
    occ = [(b.rect.bottom, b.rect.inflate(16, 0)) for b in BUILDINGS]
    occ += [(y + 4, pygame.Rect(x - 50, y - 95, 100, 92)) for x, y in TREES]
    occ += [(y + 4, pygame.Rect(x - 12, y - 86, 24, 90)) for x, y in LAMPS]
    occ.append((WELCOME_SIGN.bottom, WELCOME_SIGN))
    return occ


def town_lights(surf, cam, slot, ticks):
    """Night overlay plus glowing windows, lamps and neon."""
    ox, oy = cam
    alpha = [0, 18, 85, 150][slot]
    if not alpha:
        return
    w, h = surf.get_size()
    dark = pygame.Surface((w, h), pygame.SRCALPHA)
    dark.fill((12, 14, 55, alpha))
    surf.blit(dark, (0, 0))
    if slot < 2:
        return
    view = pygame.Rect(ox - 100, oy - 100, w + 200, h + 200)
    glow = _glow_sprite(90, (255, 210, 120))
    for x, y in LAMPS:
        if view.collidepoint(x, y):
            surf.blit(glow, (x - ox - 90, y - oy - 74 - 90), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(surf, (255, 240, 200), (x - ox, y - oy - 74), 7)
    for b in BUILDINGS:
        if not view.colliderect(b.rect):
            continue
        for wr in window_rects(b):
            r = wr.move(-ox, -oy)
            pygame.draw.rect(surf, (250, 215, 130), r, border_radius=2)
            pygame.draw.rect(surf, (255, 235, 170), r.inflate(-12, -12), border_radius=2)
        if b.key == "ballpark":
            r = b.rect
            for fx_, fy_ in ((r.x + 60, r.y + 52), (r.right - 60, r.y + 52), (r.x + 60, r.bottom - 68), (r.right - 60, r.bottom - 68)):
                surf.blit(_glow_sprite(120, (230, 230, 200)), (fx_ - ox - 120, fy_ - oy - 120), special_flags=pygame.BLEND_RGB_ADD)
        if b.key == "club":
            pulse = 0.6 + 0.4 * math.sin(ticks / 300)
            neon = _glow_sprite(150, (int(255 * pulse), 60, int(190 * pulse)))
            sc = _layout(b)[0].center
            surf.blit(neon, (sc[0] - ox - 150, sc[1] - oy - 150), special_flags=pygame.BLEND_RGB_ADD)


def _glow_sprite(r, col):
    key = ("glow", r, col)
    g = _cache.get(key)
    if g is None:
        g = pygame.Surface((r * 2, r * 2))
        for i in range(r, 0, -2):
            t = (1 - i / r) ** 2
            pygame.draw.circle(g, tuple(int(c * t * 0.55) for c in col), (r, r), i)
        _cache[key] = g
    return g


def rain(surf, ticks, rng=random.Random(3)):
    w, h = surf.get_size()
    tint = pygame.Surface((w, h), pygame.SRCALPHA)
    tint.fill((60, 70, 100, 50))
    surf.blit(tint, (0, 0))
    for i in range(220):
        x = (i * 97 + ticks * 0.25) % (w + 100) - 50
        y = (i * 53 + ticks * 0.9) % (h + 40) - 20
        pygame.draw.line(surf, (190, 205, 235), (x, y), (x - 4, y + 14), 1)


# ---- interiors ---------------------------------------------------------------------
def _floor(s, room: Room, rng):
    w, h = room.size
    kind = room.floor
    if kind == "wood":
        for y in range(0, h, 22):
            off = rng.randint(0, 120)
            for x in range(-off, w, 160):
                c = shade((150, 108, 72), rng.uniform(0.88, 1.08))
                grad(s, (x, y, 158, 21), shade(c, 1.05), shade(c, 0.92))
                for _ in range(6):
                    gx = rng.randint(x, x + 150)
                    pygame.draw.line(s, shade(c, 0.85), (gx, y + 4), (gx + 30, y + 6))
    elif kind in ("tile", "lino", "diner"):
        size = 48 if kind != "diner" else 40
        s.fill((180, 182, 186))
        for y in range(0, h, size):
            for x in range(0, w, size):
                if kind == "diner":
                    c = (235, 235, 230) if (x // size + y // size) % 2 == 0 else (50, 50, 58)
                else:
                    c = shade((228, 230, 232) if kind == "tile" else (205, 210, 205), rng.uniform(0.96, 1.03))
                grad(s, (x + 1, y + 1, size - 2, size - 2), shade(c, 1.03), shade(c, 0.95))
    elif kind == "carpet":
        s.fill((150, 110, 125))
        noise(s, (0, 0, w, h), (150, 110, 125), 0.08, w * h // 12, rng, (0.6, 1.5))
    elif kind == "club":
        s.fill((28, 20, 34))
        noise(s, (0, 0, w, h), (40, 28, 48), 0.25, w * h // 30, rng, (0.5, 1.2))
    elif kind == "field":
        s.fill((80, 150, 75))
        for x in range(0, w, 60):
            alpha_rect(s, (255, 255, 255, 14) if (x // 60) % 2 else (0, 0, 0, 10), (x, 0, 60, h))
        noise(s, (0, 0, w, h), (80, 150, 75), 0.08, w * h // 40, rng, (0.5, 1.4))
    elif kind == "dark":
        s.fill((48, 46, 52))
        noise(s, (0, 0, w, h), (55, 52, 60), 0.12, w * h // 25, rng, (0.5, 1.3))


def _walls(s, room: Room):
    w, h = room.size
    grad(s, (0, 0, w, 52), shade(room.wall, 1.05), shade(room.wall, 0.85))
    grad(s, (0, 52, w, 8), (60, 45, 35), (40, 30, 25))
    alpha_rect(s, (0, 0, 0, 60), (0, 60, w, 10))
    for x0, x1 in ((0, 18), (w - 18, w)):
        grad(s, (x0, 0, x1 - x0, h), shade(room.wall, 0.75), shade(room.wall, 0.6), horizontal=True)
    grad(s, (0, h - 18, w, 18), shade(room.wall, 0.7), shade(room.wall, 0.55))
    door = pygame.Rect(w // 2 - 60, h - 18, 120, 18)
    pygame.draw.rect(s, (160, 60, 60), door)
    alpha_rect(s, (255, 255, 255, 40), door.inflate(-20, -10), 4)


def _pillow(s, r):
    grad(s, r, (250, 250, 248), (215, 215, 212), 10)


def paint_furniture(s, kind, r, rng):
    r = pygame.Rect(r)
    if kind in ("tilefloor", "rug", "dancefloor", "menuboard", "whiteboard", "shelf_back"):
        if kind == "tilefloor":
            pygame.draw.rect(s, (190, 198, 204), r)
            for y in range(r.top, r.bottom, 40):
                for x in range(r.left, r.right, 40):
                    grad(s, (x + 1, y + 1, 38, 38), (232, 240, 245), (205, 215, 222))
        elif kind == "rug":
            grad(s, r, (170, 70, 80), (130, 45, 60), 14)
            pygame.draw.rect(s, (225, 190, 120), r.inflate(-24, -24), 3, border_radius=10)
        elif kind == "menuboard":
            grad(s, r, (40, 40, 44), (25, 25, 28), 6)
            t = font(16).render("BURGERS · FRIES · SHAKES · PICKLES & ICE CREAM", True, (250, 230, 160))
            s.blit(t, t.get_rect(center=r.center))
        elif kind == "whiteboard":
            grad(s, r, (250, 250, 250), (225, 228, 232), 4)
            t = font(13, False).render("Q3 SYNERGY >>> profit", True, (60, 90, 200))
            s.blit(t, t.get_rect(center=r.center))
        elif kind == "shelf_back":
            grad(s, r, (220, 225, 222), (190, 195, 190), 4)
            for i in range(30):
                bx = r.x + 8 + i * 15
                pygame.draw.rect(s, rng.choice([(220, 80, 90), (80, 150, 220), (240, 200, 80), (120, 200, 140)]),
                                 (bx, r.y + 8 + (i % 2) * 24, 11, 18), border_radius=2)
        return
    if kind == "wall":
        grad(s, r, (200, 185, 165), (150, 135, 120), horizontal=True)
        return
    if kind not in ("diamond", "scoreboard"):
        soft_shadow(s, r, (6, 9), 70, 10, 2)
    if kind in ("bed", "bed_red"):
        sheet = (90, 130, 205) if kind == "bed" else (205, 60, 85)
        grad(s, r, (120, 85, 60), (85, 58, 40), 12)
        grad(s, r.inflate(-12, -12), (248, 248, 245), (225, 225, 222), 10)
        _pillow(s, (r.x + 16, r.y + 14, r.w // 2 - 22, 34))
        _pillow(s, (r.centerx + 6, r.y + 14, r.w // 2 - 22, 34))
        blanket = pygame.Rect(r.x + 8, r.y + 58, r.w - 16, r.h - 66)
        grad(s, blanket, shade(sheet, 1.15), shade(sheet, 0.8), 10)
        grad(s, (blanket.x, blanket.y, blanket.w, 12), (250, 250, 248), (220, 220, 218), 6)
    elif kind == "crib":
        grad(s, r, (245, 240, 230), (215, 205, 190), 10)
        grad(s, r.inflate(-14, -14), (190, 220, 245), (160, 195, 230), 8)
        for x in range(r.x + 6, r.right - 4, 10):
            pygame.draw.line(s, (235, 228, 215), (x, r.y + 2), (x, r.y + 8), 3)
            pygame.draw.line(s, (235, 228, 215), (x, r.bottom - 8), (x, r.bottom - 2), 3)
        ball(s, (250, 210, 90), (r.right - 18, r.y + 18), 6, steps=4)
    elif kind == "mirror":
        grad(s, r, (215, 180, 110), (170, 135, 70), 8)
        grad(s, r.inflate(-10, -10), (215, 235, 245), (160, 190, 210), 6)
        pygame.draw.line(s, (240, 250, 255), (r.x + 14, r.bottom - 10), (r.x + 30, r.y + 8), 3)
    elif kind == "fridge":
        grad(s, r, (250, 250, 252), (205, 208, 214), 10, horizontal=True)
        pygame.draw.line(s, (185, 188, 195), (r.x + 4, r.y + 48), (r.right - 4, r.y + 48), 2)
        pygame.draw.rect(s, (170, 172, 180), (r.right - 16, r.y + 14, 5, 26), border_radius=2)
        pygame.draw.rect(s, (170, 172, 180), (r.right - 16, r.y + 60, 5, 40), border_radius=2)
        for i, c in enumerate([(230, 80, 90), (80, 170, 220), (250, 200, 80)]):
            ball(s, c, (r.x + 18 + i * 16, r.y + 76 + (i % 2) * 10), 5, steps=3)
    elif kind == "kitchen":
        grad(s, r, (210, 205, 198), (170, 165, 158), 6)
        grad(s, (r.x, r.y, r.w, 18), (235, 232, 228), (205, 200, 195), 6)
        for i in range(2):
            pygame.draw.circle(s, (50, 50, 55), (r.x + 40 + i * 60, r.y + 46), 16)
            pygame.draw.circle(s, (80, 80, 88), (r.x + 40 + i * 60, r.y + 46), 10)
    elif kind == "couch":
        grad(s, r, (120, 85, 150), (80, 55, 105), 16)
        grad(s, (r.x, r.y, r.w, 26), (140, 105, 170), (105, 75, 135), 12)
        for i in range(2):
            grad(s, (r.x + 18 + i * (r.w - 36) // 2, r.y + 28, (r.w - 44) // 2, r.h - 40),
                 (150, 115, 180), (110, 80, 140), 10)
        grad(s, (r.x, r.y + 10, 18, r.h - 14), (110, 78, 140), (80, 55, 105), 8)
        grad(s, (r.right - 18, r.y + 10, 18, r.h - 14), (110, 78, 140), (80, 55, 105), 8)
    elif kind == "shower":
        grad(s, r, (215, 228, 236), (180, 196, 206), 8)
        alpha_rect(s, (170, 215, 240, 110), r.inflate(-14, -14), 6)
        pygame.draw.circle(s, (180, 185, 195), (r.x + 30, r.y + 24), 12)
        for i in range(8):
            pygame.draw.circle(s, (120, 125, 135), (r.x + 24 + (i % 4) * 4, r.y + 20 + (i // 4) * 6), 1)
        pygame.draw.circle(s, (120, 130, 140), r.center, 6)
    elif kind == "toilet":
        grad(s, (r.x + 8, r.y, r.w - 16, 22), (250, 250, 252), (215, 218, 224), 6)
        pygame.draw.ellipse(s, (240, 242, 246), (r.x, r.y + 16, r.w, r.h - 16))
        pygame.draw.ellipse(s, (205, 225, 235), (r.x + 12, r.y + 26, r.w - 24, r.h - 36))
    elif kind == "sink":
        grad(s, r, (245, 245, 248), (210, 212, 218), 10)
        pygame.draw.ellipse(s, (200, 215, 225), r.inflate(-18, -16))
        pygame.draw.rect(s, (180, 185, 195), (r.centerx - 3, r.y + 2, 6, 12), border_radius=2)
    elif kind == "plant":
        grad(s, (r.x + 8, r.y + r.h // 2, r.w - 16, r.h // 2), (190, 110, 70), (140, 75, 45), 6)
        for i in range(9):
            a = i / 9 * math.tau
            ball(s, (70, 140, 70), (r.centerx + math.cos(a) * 12, r.y + 14 + math.sin(a) * 9), 10, steps=4)
    elif kind in ("counter_red", "counter_green", "bar"):
        top = {"counter_red": (200, 55, 60), "counter_green": (60, 165, 105), "bar": (120, 75, 45)}[kind]
        grad(s, r, shade(top, 0.95), shade(top, 0.62), 8)
        grad(s, (r.x, r.y, r.w, 18), (240, 238, 232) if kind != "bar" else (160, 110, 70),
             (205, 200, 192) if kind != "bar" else (110, 72, 45), 8)
        if kind == "bar":
            for i in range(10):
                bx = r.x + 20 + i * 25
                c = rng.choice([(90, 160, 90), (170, 80, 60), (200, 190, 120), (120, 120, 200)])
                pygame.draw.rect(s, c, (bx, r.y - 28, 9, 26), border_radius=3)
                pygame.draw.rect(s, shade(c, 1.3), (bx + 2, r.y - 24, 2, 16))
    elif kind in ("desk", "desk_white"):
        top = (150, 110, 75) if kind == "desk" else (240, 242, 246)
        grad(s, r, shade(top, 1.05), shade(top, 0.75), 6)
        grad(s, (r.centerx - 26, r.y - 26, 52, 34), (50, 55, 65), (30, 32, 40), 4)
        grad(s, (r.centerx - 22, r.y - 22, 44, 26), (110, 170, 230), (60, 110, 170), 3)
        pygame.draw.rect(s, (60, 62, 70), (r.centerx - 30, r.y + 18, 60, 10), border_radius=3)
    elif kind == "dj":
        grad(s, r, (40, 40, 48), (20, 20, 26), 10)
        for i in range(2):
            c = (r.x + 50 + i * 120, r.centery)
            pygame.draw.circle(s, (15, 15, 18), c, 26)
            pygame.draw.circle(s, (60, 60, 70), c, 8)
        for i in range(8):
            pygame.draw.circle(s, [(255, 60, 160), (60, 200, 255), (255, 220, 60)][i % 3], (r.x + 90 + i * 6, r.y + 14), 2)
    elif kind == "vip":
        grad(s, r, (130, 30, 70), (80, 15, 40), 18)
        grad(s, r.inflate(-30, -30), (60, 50, 55), (35, 28, 32), 30)
        pygame.draw.circle(s, (220, 200, 120), r.center, 6)
    elif kind == "loungetable":
        pygame.draw.ellipse(s, (50, 40, 60), r)
        pygame.draw.ellipse(s, (90, 75, 110), r.inflate(-12, -12))
        ball(s, (240, 90, 160), (r.centerx - 14, r.centery), 6, steps=4)
        ball(s, (120, 220, 240), (r.centerx + 14, r.centery + 4), 6, steps=4)
    elif kind == "stool":
        ball(s, (200, 55, 60), r.center, r.w // 2, steps=5)
    elif kind == "table":
        grad(s, r, (240, 235, 225), (205, 198, 186), 14)
        for dx in (-30, 30):
            pygame.draw.ellipse(s, (250, 250, 250), (r.centerx + dx - 14, r.centery - 10, 28, 20))
            ball(s, (200, 140, 70), (r.centerx + dx, r.centery - 1), 6, steps=3)
    elif kind == "cooler":
        grad(s, r, (220, 225, 235), (180, 185, 195), 8)
        ball(s, (120, 190, 240), (r.centerx, r.y + 14), 14, steps=5)
    elif kind == "shelf":
        grad(s, r, (160, 120, 85), (115, 82, 56), 4)
        for y in range(r.y + 8, r.bottom - 8, 26):
            for x in range(r.x + 5, r.right - 6, 12):
                pygame.draw.rect(s, rng.choice([(220, 80, 90), (80, 150, 220), (240, 200, 80), (240, 240, 240)]),
                                 (x, y, 9, 18), border_radius=2)
    elif kind == "exambed":
        grad(s, r, (200, 205, 215), (160, 165, 175), 10)
        grad(s, r.inflate(-12, -12), (120, 190, 200), (90, 160, 170), 8)
        alpha_rect(s, (255, 255, 255, 120), (r.x + 30, r.y + 10, r.w - 60, r.h - 20), 4)
    elif kind == "bench":
        grad(s, r, (100, 150, 200), (70, 110, 160), 10)
    elif kind == "piercechair":
        grad(s, r, (40, 40, 45), (20, 20, 24), 18)
        grad(s, r.inflate(-16, -16), (160, 30, 45), (110, 20, 30), 14)
        pygame.draw.circle(s, (230, 230, 240), (r.right + 16, r.y + 20), 10)
    elif kind == "display":
        grad(s, r, (30, 30, 34), (15, 15, 18), 6)
        alpha_rect(s, (200, 220, 240, 60), r.inflate(-8, -8), 4)
        for i in range(12):
            ball(s, (215, 220, 230), (r.x + 14 + i * 17, r.centery + (i % 2) * 6), 4, steps=3)
    elif kind == "bed_luxe":
        grad(s, r, (70, 50, 40), (40, 28, 22), 14)
        grad(s, (r.x, r.y - 14, r.w, 24), (90, 65, 50), (55, 40, 30), 10)
        grad(s, r.inflate(-12, -12), (250, 248, 242), (228, 222, 214), 12)
        for i in range(3):
            _pillow(s, (r.x + 14 + i * (r.w - 28) // 3, r.y + 12, (r.w - 40) // 3, 30))
        blanket = pygame.Rect(r.x + 8, r.y + 54, r.w - 16, r.h - 62)
        grad(s, blanket, (220, 190, 120), (170, 135, 70), 10)
        grad(s, (blanket.x, blanket.y, blanket.w, 12), (250, 248, 242), (225, 220, 212), 6)
        for i in range(6):
            pygame.draw.circle(s, (240, 215, 150), (blanket.x + 20 + i * (blanket.w - 40) // 5, blanket.centery + 6), 2)
    elif kind == "crib_nursery":
        alpha_ellipse(s, (250, 200, 230, 90), r.inflate(70, 60))
        grad(s, r, (250, 245, 235), (225, 215, 200), 12)
        grad(s, r.inflate(-14, -14), (250, 210, 230), (230, 180, 210), 10)
        for x in range(r.x + 6, r.right - 4, 10):
            pygame.draw.line(s, (240, 232, 220), (x, r.y + 2), (x, r.y + 8), 3)
        for i, c in enumerate([(250, 210, 90), (140, 200, 240), (240, 140, 180), (150, 220, 160)]):
            pygame.draw.line(s, (200, 200, 205), (r.centerx, r.y - 10), (r.x + 20 + i * 24, r.y + 14), 1)
            ball(s, c, (r.x + 20 + i * 24, r.y + 16), 6, steps=4)
    elif kind == "kitchen_pro":
        grad(s, r, (70, 70, 78), (40, 40, 46), 6)
        grad(s, (r.x, r.y, r.w, 18), (235, 235, 238), (200, 200, 205), 6)
        for i in range(4):
            cx, cy = r.x + 28 + (i % 2) * 44, r.y + 34 + (i // 2) * 26
            pygame.draw.circle(s, (30, 30, 34), (cx, cy), 11)
            pygame.draw.circle(s, (200, 70, 50) if i == 0 else (70, 70, 78), (cx, cy), 6)
        grad(s, (r.right - 70, r.y + 24, 56, 46), (180, 185, 195), (130, 135, 145), 6)
        pygame.draw.rect(s, (60, 60, 66), (r.right - 62, r.y + 30, 40, 22), border_radius=3)
    elif kind == "tv":
        grad(s, (r.x + 30, r.bottom - 6, r.w - 60, 10), (120, 90, 60), (80, 60, 40), 4)
        grad(s, r, (30, 30, 36), (15, 15, 18), 6)
        grad(s, r.inflate(-8, -8), (60, 110, 170), (30, 60, 110), 4)
        pygame.draw.polygon(s, (110, 160, 210), [(r.x + 20, r.bottom - 5), (r.x + 60, r.y + 5), (r.x + 80, r.y + 5), (r.x + 40, r.bottom - 5)])
    elif kind == "gym":
        grad(s, r, (60, 60, 70), (40, 40, 48), 10)
        grad(s, (r.x + 10, r.y + 10, 70, r.h - 20), (50, 50, 56), (30, 30, 34), 8)
        pygame.draw.rect(s, (90, 90, 100), (r.x + 18, r.y + 18, 54, 8), border_radius=3)
        for i in range(3):
            y = r.y + 30 + i * 30
            pygame.draw.line(s, (180, 185, 195), (r.x + 100, y), (r.right - 14, y), 4)
            for x in (r.x + 100, r.right - 14):
                pygame.draw.circle(s, (40, 40, 46), (x, y), 9)
    elif kind == "shower_rain":
        grad(s, r, (220, 225, 230), (175, 185, 195), 8)
        grad(s, r.inflate(-10, -10), (60, 64, 70), (40, 44, 50), 6)
        alpha_rect(s, (170, 215, 240, 90), r.inflate(-14, -14), 6)
        pygame.draw.rect(s, (200, 205, 215), (r.centerx - 30, r.y + 18, 60, 60), border_radius=8)
        for i in range(36):
            pygame.draw.circle(s, (120, 125, 135), (r.centerx - 24 + (i % 6) * 10, r.y + 24 + (i // 6) * 10), 1)
        for i in range(10):
            pygame.draw.line(s, (200, 230, 250), (r.x + 30 + i * 10, r.y + 90), (r.x + 26 + i * 10, r.y + 130), 1)
    elif kind == "hottub":
        grad(s, r, (150, 110, 80), (105, 75, 55), 26)
        inner = r.inflate(-28, -28)
        grad(s, inner, (90, 200, 220), (40, 140, 180), 22)
        for i in range(18):
            rr = random.Random(i)
            pygame.draw.circle(s, (220, 245, 250), (rr.randint(inner.x + 10, inner.right - 10),
                                                    rr.randint(inner.y + 10, inner.bottom - 10)), rr.randint(2, 5), 1)
        alpha_rect(s, (255, 255, 255, 50), (inner.x + 10, inner.y + 8, inner.w - 20, 10), 6)
    elif kind == "diamond":
        cx, cy = r.centerx, r.centery
        pts = [(cx, r.bottom), (r.right, cy), (cx, r.top), (r.x, cy)]
        pygame.draw.polygon(s, (190, 140, 90), pts)
        noise(s, r.inflate(-160, -140), (190, 140, 90), 0.08, 1500, rng, (0.5, 1.5))
        inner = [(cx, r.bottom - 90), (r.right - 110, cy), (cx, r.top + 90), (r.x + 110, cy)]
        pygame.draw.polygon(s, (85, 155, 80), inner)
        for x, y in pts:
            soft_shadow(s, (x - 12, y - 12, 24, 24), (2, 3), 40, 4, 1)
            pygame.draw.rect(s, (250, 250, 250), (x - 12, y - 12, 24, 24), border_radius=3)
        pygame.draw.circle(s, (180, 130, 85), (cx, cy + 10), 30)
        pygame.draw.rect(s, (250, 250, 250), (cx - 10, cy + 6, 20, 6))
        for x0 in (r.x, r.right):
            pygame.draw.line(s, (250, 250, 250), (cx, r.bottom), (x0 + (cx - x0) * -0.3, cy - (r.bottom - cy) * 1.3), 3)
    elif kind == "bleachers":
        for i in range(5):
            grad(s, (r.x, r.y + i * 28, r.w, 26), (200, 205, 212), (150, 155, 165), 4)
        crowd = random.Random(9)
        for _ in range(420):
            x, y = crowd.randint(r.x + 6, r.right - 6), r.y + crowd.randint(0, 4) * 28 + 6
            c = crowd.choice([(240, 200, 160), (120, 80, 50), (200, 60, 80), (60, 110, 200), (250, 250, 250)])
            ball(s, c, (x, y), 6, steps=3)
    elif kind == "scoreboard":
        grad(s, r, (30, 34, 40), (15, 18, 22), 8)
    elif kind == "dugout":
        grad(s, r, (40, 90, 160), (25, 60, 115), 10)
        grad(s, r.inflate(-12, -16), (30, 30, 36), (15, 15, 18), 6)
        for i in range(5):
            pygame.draw.rect(s, (200, 170, 120), (r.x + 16 + i * 34, r.bottom - 14, 6, 26), border_radius=2)
    elif kind == "cage":
        grad(s, r, (90, 150, 85), (70, 130, 70), 6)
        pygame.draw.rect(s, (190, 140, 90), r.inflate(-60, -60), border_radius=10)
        for x in range(r.x, r.right + 1, 14):
            pygame.draw.line(s, (60, 60, 66), (x, r.y), (x, r.bottom), 1)
        for y in range(r.y, r.bottom + 1, 14):
            pygame.draw.line(s, (60, 60, 66), (r.x, y), (r.right, y), 1)
        grad(s, (r.centerx - 22, r.y + 10, 44, 50), (80, 80, 90), (50, 50, 58), 6)
    elif kind == "concession":
        grad(s, r, (220, 60, 50), (160, 35, 30), 8)
        for i in range(0, r.w, 20):
            col = (250, 250, 245) if (i // 20) % 2 else (220, 60, 50)
            grad(s, (r.x + i, r.y - 26, 20, 24), shade(col, 1.05), shade(col, 0.85))
        t = font(14).render("HOT DOGS · NACHOS · BEER", True, (255, 240, 200))
        s.blit(t, t.get_rect(center=(r.centerx, r.centery + 6)))
    elif kind == "counter_orange":
        grad(s, r, (230, 130, 50), (170, 85, 25), 8)
        grad(s, (r.x, r.y, r.w, 18), (240, 236, 228), (205, 198, 190), 8)
    elif kind == "toolwall":
        grad(s, r, (170, 140, 100), (130, 100, 70), 4)
        for i in range(14):
            x = r.x + 14 + i * 32
            c = rng.choice([(200, 60, 50), (240, 190, 50), (60, 120, 200), (90, 90, 100)])
            pygame.draw.rect(s, c, (x, r.y + 10, 8, 30), border_radius=2)
            pygame.draw.rect(s, (180, 185, 195), (x - 4, r.y + 38, 16, 8), border_radius=2)
    elif kind == "dresser":
        grad(s, r, (150, 105, 70), (105, 72, 48), 6)
        for i in range(2):
            pygame.draw.line(s, (90, 60, 40), (r.x + 4, r.y + 20 + i * 20), (r.right - 4, r.y + 20 + i * 20), 2)
            pygame.draw.circle(s, (220, 190, 110), (r.centerx, r.y + 12 + i * 20), 3)


def room_surface(room: Room, upgrades=()):
    key = ("room", room.key, tuple(sorted(upgrades)) if room.key == "home" else ())
    s = _cache.get(key)
    if s is None:
        s = pygame.Surface(room.size)
        rng = random.Random(room.key)
        _floor(s, room, rng)
        _walls(s, room)
        for f in sorted(room.furniture, key=lambda f: (f.solid, f.rect.bottom)):
            if f.present(upgrades):
                paint_furniture(s, f.kind_for(upgrades), f.rect, rng)
        _cache[key] = s
    return s


def room_occluders(room: Room):
    out = []
    for f in room.furniture:
        if f.occlude:
            r = f.rect
            out.append((r.bottom, pygame.Rect(r.x - 10, r.y - 4, r.w + 20, r.h + 16)))
            if f.kind in ("desk", "desk_white"):       # the monitor sticks up above the desk
                out.append((r.bottom, pygame.Rect(r.centerx - 28, r.y - 28, 56, 40)))
    return out


def dance_floor(surf, rect, ticks):
    rect = pygame.Rect(rect)
    size = 35
    for y in range(rect.top, rect.bottom, size):
        for x in range(rect.left, rect.right, size):
            i = (x // size * 3 + y // size * 5 + ticks // 400) % 7
            c = [(255, 60, 160), (60, 200, 255), (255, 220, 60), (140, 80, 255), (40, 30, 60),
                 (255, 120, 60), (60, 255, 160)][i]
            grad(surf, (x + 2, y + 2, size - 4, size - 4), shade(c, 1.1), shade(c, 0.7), 4)


def club_lights(surf, cam, ticks):
    for i in range(6):
        a = ticks / 600 + i
        x = 630 + math.cos(a * 1.3) * 200 - cam[0]
        y = 370 + math.sin(a) * 150 - cam[1]
        col = [(255, 60, 160), (60, 200, 255), (255, 230, 60)][i % 3]
        surf.blit(_glow_sprite(80, col), (x - 80, y - 80), special_flags=pygame.BLEND_RGB_ADD)


# ---- event props -----------------------------------------------------------------
EVENT_LOOKS = {
    "busker": Character("penis", "Sax", "Brown", "Black", "tophat"),
    "giveaway": Character("vagina", "Nurse Ova", "Ebony", "Black", "glasses"),
    "preacher": Character("penis", "Preacher", "Pink", "Gray", ""),
}


def draw_event(surf, ev, pos, ticks, scale):
    x, y = pos
    k = ev.key
    if k in EVENT_LOOKS:
        if k == "giveaway":
            soft_shadow(surf, (x - 70, y - 30, 70, 30), (4, 6), 60, 6, 1)
            grad(surf, (x - 70, y - 30, 70, 30), (240, 240, 245), (200, 205, 215), 6)
            for i in range(4):
                ball(surf, [(240, 90, 150), (90, 160, 240)][i % 2], (x - 60 + i * 15, y - 24), 4, steps=3)
        draw_character(surf, EVENT_LOOKS[k], (x + (10 if k == "giveaway" else 0), y), scale, ticks=ticks)
        if k == "busker":
            pygame.draw.line(surf, (220, 180, 70), (x + 20 * scale * 2.5, y - 60 * scale * 2.5),
                             (x + 34, y - 20), 5)
            for i in range(3):
                nx = x + 30 + i * 12 + math.sin(ticks / 200 + i) * 6
                ny = y - 80 - i * 14 - (ticks / 20 + i * 20) % 30
                pygame.draw.circle(surf, (40, 30, 30), (nx, ny), 4)
                pygame.draw.line(surf, (40, 30, 30), (nx + 3, ny), (nx + 3, ny - 12), 2)
        if k == "preacher":
            grad(surf, (x + 18, y - 110, 56, 40), (250, 250, 240), (215, 215, 205), 4)
            t = font(11).render("REPENT", True, (180, 30, 30))
            surf.blit(t, t.get_rect(center=(x + 46, y - 90)))
    elif k == "tacotruck":
        r = pygame.Rect(x - 90, y - 70, 180, 80)
        soft_shadow(surf, r, (6, 10), 80, 10)
        grad(surf, r, (245, 200, 70), (210, 150, 40), 14)
        grad(surf, (r.x + 30, r.y + 12, 90, 30), (60, 50, 50), (35, 30, 30), 4)
        t = font(13).render("TACOS!", True, (190, 40, 40))
        surf.blit(t, t.get_rect(center=(r.centerx, r.bottom - 16)))
        for wx in (r.x + 30, r.right - 30):
            pygame.draw.circle(surf, (30, 30, 30), (wx, r.bottom), 14)
            pygame.draw.circle(surf, (150, 150, 155), (wx, r.bottom), 6)
    elif k == "wallet":
        r = pygame.Rect(x - 14, y - 8, 28, 18)
        alpha_ellipse(surf, (0, 0, 0, 60), (x - 16, y + 4, 34, 8))
        grad(surf, r, (130, 80, 50), (95, 55, 35), 4)
        pygame.draw.rect(surf, (90, 160, 90), (x - 6, y - 12, 14, 6), border_radius=1)
        sparkle = 3 + 2 * math.sin(ticks / 150)
        pygame.draw.circle(surf, (255, 255, 220), (x + 14, y - 14), sparkle)
    elif k == "blockparty":
        for i in range(9):
            lx = x - 120 + i * 30
            ly = y - 110 + math.sin(i * 0.8) * 10
            col = [(255, 90, 160), (90, 200, 255), (255, 220, 90)][i % 3]
            surf.blit(_glow_sprite(14, col), (lx - 14, ly - 14), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(surf, col, (lx, ly), 4)
        for side in (-1, 1):
            r = pygame.Rect(x + side * 110 - 18, y - 60, 36, 60)
            grad(surf, r, (50, 50, 58), (25, 25, 30), 6)
            pygame.draw.circle(surf, (90, 90, 100), (r.centerx, r.y + 38), 12)
        for i, (dx, look) in enumerate(((-50, Character("vagina", "D1", "Tan", "Red")),
                                         (40, Character("penis", "D2", "Ebony", "Black")))):
            draw_character(surf, look, (x + dx, y + 6), scale * 0.9, ticks=ticks * 2 + i * 500)
    elif k == "puppy":
        bx, by = x, y - 14 + abs(math.sin(ticks / 150)) * -4
        alpha_ellipse(surf, (0, 0, 0, 60), (x - 22, y - 4, 44, 10))
        ball(surf, (200, 150, 100), (bx, by), 14, steps=6)
        ball(surf, (210, 160, 110), (bx + 16, by - 12), 11, steps=6)
        pygame.draw.ellipse(surf, (140, 95, 60), (bx + 18, by - 26, 9, 14))
        pygame.draw.circle(surf, (20, 20, 20), (bx + 20, by - 13), 2)
        pygame.draw.circle(surf, (30, 20, 20), (bx + 27, by - 9), 2.5)
        tail = math.sin(ticks / 80) * 6
        pygame.draw.line(surf, (190, 140, 95), (bx - 12, by - 4), (bx - 22, by - 14 + tail), 4)
    elif k == "flashsale":
        r = pygame.Rect(x - 50, y - 70, 100, 50)
        pygame.draw.rect(surf, (90, 70, 50), (x - 3, y - 22, 6, 24))
        soft_shadow(surf, r, (4, 6), 70, 6, 2)
        grad(surf, r, (250, 80, 120), (200, 40, 80), 8)
        t1 = font(14).render("50% OFF", True, (255, 255, 255))
        t2 = font(10).render("PIERCINGS", True, (255, 230, 240))
        surf.blit(t1, t1.get_rect(center=(x, r.y + 18)))
        surf.blit(t2, t2.get_rect(center=(x, r.y + 36)))
