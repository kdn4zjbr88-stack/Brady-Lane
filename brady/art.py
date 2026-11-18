"""Cartoon mascot drawing with pygame primitives (no image assets needed)."""
from __future__ import annotations

import math

import pygame

from .model import BODY_COLORS, HAIR_COLORS, Character


def _shade(color, f):
    return tuple(max(0, min(255, int(c * f))) for c in color)


def _hair_tuft(surf, color, cx, cy, width, s):
    """A row of curly bumps centred on (cx, cy)."""
    n = max(5, int(width / (12 * s)))
    for i in range(n):
        x = cx - width / 2 + (i + 0.5) * width / n
        y = cy + math.sin(i * 1.7) * 4 * s
        pygame.draw.circle(surf, color, (int(x), int(y)), int(11 * s))
        pygame.draw.circle(surf, _shade(color, 1.6), (int(x - 3 * s), int(y - 3 * s)), int(3 * s))


def _face(surf, cx, cy, s, mood, energy, outline):
    eye_dx, eye_r = 18 * s, 9 * s
    for side in (-1, 1):
        ex, ey = cx + side * eye_dx, cy
        if energy < 25:  # sleepy half-closed eyes
            pygame.draw.line(surf, outline, (ex - eye_r, ey), (ex + eye_r, ey), max(2, int(3 * s)))
        else:
            pygame.draw.circle(surf, (255, 255, 255), (int(ex), int(ey)), int(eye_r))
            pygame.draw.circle(surf, (20, 20, 20), (int(ex + 2 * s), int(ey + 1 * s)), int(eye_r * 0.5))
            pygame.draw.circle(surf, (255, 255, 255), (int(ex + 3 * s), int(ey - 2 * s)), max(1, int(2 * s)))
    my = cy + 24 * s
    w = 22 * s
    rect = pygame.Rect(0, 0, w * 2, 22 * s)
    width = max(2, int(3 * s))
    if mood >= 60:
        rect.center = (cx, my - 8 * s)
        pygame.draw.arc(surf, outline, rect, math.pi * 1.1, math.pi * 1.9, width)
    elif mood >= 30:
        pygame.draw.line(surf, outline, (cx - w * 0.6, my), (cx + w * 0.6, my), width)
    else:
        rect.center = (cx, my + 8 * s)
        pygame.draw.arc(surf, outline, rect, math.pi * 0.1, math.pi * 0.9, width)


def _status_fx(surf, cx, top, s, hygiene, infected, ticks):
    if hygiene < 30:  # stink lines
        for i, dx in enumerate((-40, 0, 40)):
            pts = []
            for k in range(8):
                y = top - 10 * s - k * 6 * s
                x = cx + dx * s + math.sin(k * 1.2 + ticks / 200 + i) * 6 * s
                pts.append((x, y))
            pygame.draw.lines(surf, (120, 170, 60), False, pts, max(2, int(3 * s)))
    if infected:  # little red bumps
        for ang in (0.6, 2.2, 3.9, 5.1):
            x = cx + math.cos(ang) * 30 * s
            y = top + 120 * s + math.sin(ang) * 30 * s
            pygame.draw.circle(surf, (210, 40, 40), (int(x), int(y)), int(5 * s))


def draw_character(surf, char: Character, center, scale=1.0, mood=70, energy=80,
                   hygiene=80, infected=False, ticks=0):
    cx, cy = center
    s = scale
    body = BODY_COLORS[char.body_color]
    hair = HAIR_COLORS[char.hair_color]
    outline = _shade(body, 0.45) if sum(body) > 200 else (15, 10, 8)
    bob = math.sin(ticks / 400) * 4 * s  # idle bobbing
    cy += bob

    if char.kind == "penis":
        shaft = pygame.Rect(0, 0, 80 * s, 170 * s)
        shaft.midbottom = (cx, cy + 60 * s)
        # base
        for side in (-1, 1):
            pygame.draw.circle(surf, _shade(body, 0.9), (int(cx + side * 42 * s), int(cy + 62 * s)), int(42 * s))
            pygame.draw.circle(surf, outline, (int(cx + side * 42 * s), int(cy + 62 * s)), int(42 * s), max(2, int(3 * s)))
        _hair_tuft(surf, hair, cx, cy + 38 * s, 150 * s, s)
        pygame.draw.rect(surf, body, shaft, border_radius=int(40 * s))
        pygame.draw.rect(surf, outline, shaft, max(2, int(3 * s)), border_radius=int(40 * s))
        head = pygame.Rect(0, 0, 96 * s, 80 * s)
        head.center = (cx, shaft.top + 30 * s)
        pygame.draw.ellipse(surf, _shade(body, 1.12), head)
        pygame.draw.ellipse(surf, outline, head, max(2, int(3 * s)))
        _face(surf, cx, shaft.top + 95 * s, s, mood, energy, outline)
        top = head.top
    else:
        outer = pygame.Rect(0, 0, 170 * s, 220 * s)
        outer.center = (cx, cy)
        _hair_tuft(surf, hair, cx, outer.top + 12 * s, 120 * s, s)
        pygame.draw.ellipse(surf, body, outer)
        pygame.draw.ellipse(surf, outline, outer, max(2, int(3 * s)))
        inner = pygame.Rect(0, 0, 44 * s, 110 * s)
        inner.center = (cx, cy + 40 * s)
        pygame.draw.ellipse(surf, (200, 90, 120), inner)
        pygame.draw.ellipse(surf, outline, inner, max(2, int(3 * s)))
        _face(surf, cx, cy - 50 * s, s, mood, energy, outline)
        top = outer.top

    _status_fx(surf, cx, top, s, hygiene, infected, ticks)
