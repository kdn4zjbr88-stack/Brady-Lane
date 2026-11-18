"""Pygame front end for Brady: character setup, a walkable town, interiors and a phone."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable

import pygame

from . import actions
from .art import draw_character, draw_person
from .model import (BODY_COLORS, CHARACTER_TYPES, GAME_LENGTH_DAYS, HAIR_COLORS, PIERCINGS,
                    SWIPES_PER_DAY, Character, GameState, Partner, piercing_label)
from .world import BUILDING_BY_KEY, BUILDINGS, ROADS, ROOMS, TOWN_SIZE, TREES, Hotspot

W, H = 1100, 720
BG = (28, 24, 36)
PANEL = (44, 38, 56)
TEXT = (238, 232, 245)
MUTED = (160, 150, 175)
ACCENT = (232, 90, 140)
GOOD = (90, 200, 130)
BAD = (230, 80, 80)
GRASS = (78, 130, 70)
ROAD = (70, 70, 78)

STAT_COLORS = {
    "health": (230, 80, 90),
    "hygiene": (90, 170, 230),
    "energy": (240, 200, 70),
    "fullness": (240, 140, 60),
    "mood": (200, 110, 230),
}
SPEED = 300
SPRITE_SCALE = 0.4
OUTFITS = [(200, 60, 90), (60, 120, 200), (40, 40, 40), (230, 200, 60), (120, 60, 180), (220, 220, 220)]
MOVE_KEYS = (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
             pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)


class Button:
    def __init__(self, rect, label, sub="", color=PANEL):
        self.rect = pygame.Rect(rect)
        self.label, self.sub, self.color = label, sub, color

    def draw(self, surf, fonts, mouse, enabled=True, selected=False):
        hover = self.rect.collidepoint(mouse) and enabled
        col = ACCENT if selected else self.color
        if hover:
            col = tuple(min(255, c + 30) for c in col)
        if not enabled:
            col = (55, 50, 62)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, (90, 80, 105), self.rect, 2, border_radius=10)
        fg = TEXT if enabled else MUTED
        lbl = fonts["md"].render(self.label, True, fg)
        if self.sub:
            surf.blit(lbl, lbl.get_rect(center=(self.rect.centerx, self.rect.centery - 9)))
            sub = fonts["xs"].render(self.sub, True, MUTED)
            surf.blit(sub, sub.get_rect(center=(self.rect.centerx, self.rect.centery + 13)))
        else:
            surf.blit(lbl, lbl.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


@dataclass
class Option:
    label: str
    sub: str
    fn: Callable[[], None] | None  # None = disabled


@dataclass
class Popup:
    title: str
    options: list[Option]
    anchor: pygame.Rect | None = None  # pop-up closes when you walk out of this


@dataclass
class Npc:
    partner: Partner
    x: float
    y: float
    phase: float
    outfit: tuple

    @property
    def zone(self):
        return pygame.Rect(self.x - 55, self.y - 55, 110, 110)


def wrap(text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if font.size(test)[0] <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class App:
    PHONE = pygame.Rect(W - 400, 80, 360, 600)

    def __init__(self, seed=None):
        pygame.init()
        pygame.display.set_caption("Brady")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.fonts = {k: pygame.font.SysFont(None, v) for k, v in
                      {"xl": 72, "lg": 40, "md": 28, "sm": 24, "xs": 20}.items()}
        self.seed = seed
        self.char = Character()
        self.scene = "setup"
        self.gs: GameState | None = None
        self.toast, self.toast_color, self.toast_until = "", BAD, 0
        self.running = True
        self.ticks = 0
        self.drag_start: int | None = None
        self.drag_x = 0

    # ================================================================ setup
    def setup_buttons(self):
        btns = {}
        for i, kind in enumerate(CHARACTER_TYPES):
            btns[("kind", kind)] = Button((180 + i * 400, 130, 340, 330), "")
        for i, name in enumerate(BODY_COLORS):
            btns[("body", name)] = Button((300 + i * 105, 500, 95, 40), name)
        for i, name in enumerate(HAIR_COLORS):
            btns[("hair", name)] = Button((300 + i * 105, 560, 95, 40), name)
        btns[("start",)] = Button((W // 2 - 110, 640, 220, 56), "Start life", color=(120, 50, 85))
        return btns

    def draw_setup(self, mouse):
        f = self.fonts
        title = f["xl"].render("BRADY", True, ACCENT)
        self.screen.blit(title, title.get_rect(center=(W // 2, 50)))
        sub = f["sm"].render("Pick your character, then keep them healthy, happy and safe for "
                             f"{GAME_LENGTH_DAYS} days. Adults only.", True, MUTED)
        self.screen.blit(sub, sub.get_rect(center=(W // 2, 95)))
        for key, b in self.setup_buttons().items():
            if key[0] == "kind":
                b.draw(self.screen, f, mouse, selected=self.char.kind == key[1])
                preview = Character(key[1], self.char.name, self.char.body_color, self.char.hair_color)
                draw_character(self.screen, preview, (b.rect.centerx, b.rect.centery - 5), 0.95,
                               ticks=self.ticks)
                lbl = f["md"].render(key[1].capitalize(), True, TEXT)
                self.screen.blit(lbl, lbl.get_rect(center=(b.rect.centerx, b.rect.bottom - 18)))
            elif key[0] == "body":
                b.draw(self.screen, f, mouse, selected=self.char.body_color == key[1])
            elif key[0] == "hair":
                b.draw(self.screen, f, mouse, selected=self.char.hair_color == key[1])
            else:
                b.draw(self.screen, f, mouse)
        for y, txt in ((520, "Skin"), (580, "Hair")):
            t = f["md"].render(txt, True, MUTED)
            self.screen.blit(t, t.get_rect(midright=(285, y)))
        name = f["md"].render(f"Name: {self.char.name}_  (type to rename)", True, TEXT)
        self.screen.blit(name, name.get_rect(midleft=(30, 668)))

    def click_setup(self, pos):
        for key, b in self.setup_buttons().items():
            if not b.hit(pos):
                continue
            if key[0] == "kind":
                self.char.kind = key[1]
            elif key[0] == "body":
                self.char.body_color = key[1]
            elif key[0] == "hair":
                self.char.hair_color = key[1]
            elif key[0] == "start":
                self.start_game()

    def key_setup(self, e):
        if e.key == pygame.K_BACKSPACE:
            self.char.name = self.char.name[:-1]
        elif e.key == pygame.K_RETURN:
            self.start_game()
        elif e.unicode and e.unicode.isprintable() and len(self.char.name) < 14:
            self.char.name += e.unicode

    def start_game(self):
        self.char.name = self.char.name.strip() or "Brady"
        self.gs = GameState(character=self.char, rng=random.Random(self.seed))
        self.gs.say(f"Welcome to town, {self.char.name}! Walk with WASD/arrows. Press P for your phone.")
        self.room = "town"
        self.px, self.py = BUILDING_BY_KEY["home"].outside_spot
        self.npcs: list[Npc] = []
        self.popup: Popup | None = None
        self.phone_open = False
        self.phone_tab = "swipe"
        self.card: Partner | None = None
        self.scene = "world"

    # ================================================================ world
    def room_size(self):
        return TOWN_SIZE if self.room == "town" else ROOMS[self.room].size

    def solids(self):
        if self.room == "town":
            return [b.rect for b in BUILDINGS]
        return ROOMS[self.room].solids()

    def hotspots(self) -> list[Hotspot]:
        if self.room == "town":
            return [Hotspot(f"door:{b.key}", b.door_zone, b.name) for b in BUILDINGS]
        spots = list(ROOMS[self.room].hotspots)
        if self.room == "club":
            spots = [Hotspot(f"npc:{i}", n.zone, n.partner.name) for i, n in enumerate(self.npcs)] + spots
        return spots

    def feet(self):
        return pygame.Rect(self.px - 16, self.py - 10, 32, 20)

    def move(self, dt):
        if self.phone_open:
            return
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if not (dx or dy):
            return
        self.step(dx, dy, dt)

    def step(self, dx, dy, dt):
        norm = math.hypot(dx, dy)
        rw, rh = self.room_size()
        wall = 0 if self.room == "town" else 18
        for axis, d in (("x", dx), ("y", dy)):
            if not d:
                continue
            old = (self.px, self.py)
            if axis == "x":
                self.px = max(wall + 16, min(rw - wall - 16, self.px + d / norm * SPEED * dt))
            else:
                self.py = max(wall + 30, min(rh - wall - 10, self.py + d / norm * SPEED * dt))
            if self.feet().collidelist(self.solids()) != -1:
                self.px, self.py = old
        # walking out of an anchored pop-up closes it
        if self.popup and self.popup.anchor and not self.popup.anchor.collidepoint(self.px, self.py):
            self.popup = None

    def current_spot(self) -> Hotspot | None:
        for h in self.hotspots():
            if h.zone.collidepoint(self.px, self.py):
                return h
        return None

    def warp(self, room, pos=None):
        self.room = room
        self.popup = None
        if room == "town":
            self.px, self.py = pos
        else:
            self.px, self.py = ROOMS[room].spawn
        if room == "club":
            self.spawn_club_npcs()

    def spawn_club_npcs(self):
        rng = self.gs.rng
        anat = None if self.gs.show_me == "everyone" else self.gs.show_me
        self.npcs = [Npc(Partner.random(rng, anat), rng.randint(420, 800), rng.randint(230, 500),
                         rng.random() * 6, rng.choice(OUTFITS)) for _ in range(rng.randint(3, 4))]

    # ---- turning hotspots into choices ---------------------------------
    def do(self, fn, *args, then=None):
        def run():
            err = fn(self.gs, *args)
            if err:
                self.show_toast(err)
            elif then:
                then()
            if self.gs.game_over:
                self.scene = "over"
        return run

    def options_for(self, spot: Hotspot) -> Popup | None:
        gs, key, A = self.gs, spot.key, actions
        if key.startswith("door:"):
            b = BUILDING_BY_KEY[key[5:]]
            if b.key == "club" and not gs.is_night_time:
                return Popup(b.name, [Option("Closed", "Opens in the evening", None)])
            if b.key in ("office", "clinic", "diner", "pharmacy", "studio") and gs.time_name == "Night":
                return Popup(b.name, [Option("Closed", "Come back in the morning", None)])
            if b.key == "apartments" and not gs.date:
                return Popup(b.name, [Option("Locked", "Nobody's expecting you. Text a match.", None)])
            sub = f"{gs.date.name} is waiting" if b.key == "apartments" else ""
            return Popup(b.name, [Option("Go inside", sub, lambda: self.warp(b.key))])
        if key == "exit":
            b = BUILDING_BY_KEY[self.room]
            return Popup("Exit", [Option("Leave", "Back to town", lambda: self.warp("town", b.outside_spot))])
        simple = {
            "sleep": ("Your bed", "Sleep", "Skip to morning, full energy", A.sleep),
            "mirror": ("Mirror", "Check yourself out", "See your charm", A.mirror),
            "snack": ("Fridge", "Grab a snack", f"${A.SNACK_PRICE} · +20 fullness", A.snack),
            "shower": ("Bathroom", "Take a shower", "Hygiene to 100", A.shower),
            "pee": ("Bathroom", "Use the toilet", "", A.pee),
            "eat": ("Diner", "Order the burger meal", f"${A.MEAL_PRICE} · +45 fullness", A.eat),
            "work": ("Office", "Work a shift", f"+${A.WORK_PAY} · tiring", A.work),
            "clinic": ("Doctor", "STI test & treatment", f"${A.CLINIC_PRICE}", A.clinic),
            "dance": ("Dance floor", "Dance", "+Mood, sweaty", A.dance),
            "bar": ("Bar", "Order a drink", f"${A.DRINK_PRICE} · +Mood", A.drink),
        }
        if key in simple:
            title, label, sub, fn = simple[key]
            return Popup(title, [Option(label, sub, self.do(fn))])
        if key == "pharmacy":
            return Popup("Pharmacy", [
                Option(f"Condoms x{A.CONDOM_PACK_SIZE}", f"${A.CONDOM_PACK_PRICE}", self.do(A.buy_condoms)),
                Option("Pregnancy test", f"${A.TEST_PRICE}", self.do(A.pregnancy_test)),
                Option("Morning-after pill", f"${A.PILL_PRICE} · works best within a day",
                       self.do(A.morning_after_pill)),
            ])
        if key == "studio":
            return Popup("Piercings", [
                Option(piercing_label(n, gs.character.kind), f"${p} · +{c} charm",
                       self.do(A.get_piercing, n) if n not in gs.piercings else None)
                for n, (p, c) in PIERCINGS.items()])
        if key.startswith("npc:"):
            p = self.npcs[int(key[4:])].partner
            title = f"{p.name}, {p.age} · {p.vibe}"
            if p in gs.matches:
                go = self.do(A.go_home_with, p, then=lambda: self.warp("apartments"))
                return Popup(title, [Option("Go home with them", "Things are heating up", go)])
            return Popup(title, [Option("Chat them up", f"Your charm: {gs.charm}", self.do(A.chat_up, p))])
        if key == "bed":
            p = gs.date
            if not p:
                return Popup("Their bed", [Option("Nobody here", "Time to head home", None)])
            n = gs.condoms

            def cuddle(g):
                g.say(f"You and {p.name} cuddle and talk till late. Cute.")
                g.adjust(mood=8)
                g.date = None
                g.advance()

            return Popup(f"Get frisky with {p.name}?", [
                Option("Use a condom", f"{n} left", self.do(A.hook_up, p, "condom") if n else None),
                Option("No condom", "Risky...", self.ask_finish),
                Option("Just cuddle", "Call it a night", self.do(cuddle)),
            ])
        return None

    def ask_finish(self):
        gs, p = self.gs, self.gs.date
        if gs.energy < 15:
            return self.show_toast("Too tired for that right now.")
        if not actions.can_conceive(gs, p):
            return self.do(actions.hook_up, p, "inside")()
        if gs.character.kind == "penis":
            a, b = "Pull out", "Finish inside"
        else:
            a, b = "Ask them to pull out", "Let them finish inside"
        spot = self.current_spot()
        self.popup = Popup("When it's time...", [
            Option(a, "Lower risk, not zero", self.close_after(self.do(actions.hook_up, p, "pull_out"))),
            Option(b, "Highest pregnancy risk", self.close_after(self.do(actions.hook_up, p, "inside"))),
        ], anchor=spot.zone if spot else None)

    def close_after(self, fn):
        def run():
            self.popup = None
            fn()
        return run

    def active_popup(self) -> Popup | None:
        if self.popup:
            return self.popup
        spot = self.current_spot()
        return self.options_for(spot) if spot else None

    def popup_buttons(self, popup):
        x, w, h = W - 400, 380, 52
        top = H - 20 - len(popup.options) * (h + 8)
        return [Button((x, top + i * (h + 8), w, h), f"{i + 1}. {o.label}", o.sub)
                for i, o in enumerate(popup.options)]

    def choose(self, i):
        popup = self.active_popup()
        if popup and 0 <= i < len(popup.options) and popup.options[i].fn:
            popup.options[i].fn()

    # ---- drawing -------------------------------------------------------
    def camera(self):
        rw, rh = self.room_size()
        cx = (rw - W) / 2 if rw <= W else max(0, min(rw - W, self.px - W / 2))
        cy = (rh - H) / 2 - 20 if rh <= H else max(0, min(rh - H, self.py - H / 2))
        return int(cx), int(cy)

    def draw_town(self, cam):
        s, f = self.screen, self.fonts
        ox, oy = cam
        s.fill(GRASS)
        for r in ROADS:
            pygame.draw.rect(s, ROAD, r.move(-ox, -oy))
        for x in range(0, TOWN_SIZE[0], 80):
            pygame.draw.rect(s, (220, 210, 120), (x - ox, 816 - oy, 40, 6))
        for y in range(0, TOWN_SIZE[1], 80):
            pygame.draw.rect(s, (220, 210, 120), (1297 - ox, y - oy, 6, 40))
        for tx, ty in TREES:
            pygame.draw.circle(s, (50, 95, 50), (tx - ox, ty - oy), 38)
            pygame.draw.circle(s, (70, 120, 65), (tx - ox - 8, ty - oy - 8), 24)
        lit = self.gs.is_night_time
        for b in BUILDINGS:
            r = b.rect.move(-ox, -oy)
            pygame.draw.rect(s, (40, 70, 40), r.move(8, 8), border_radius=6)
            pygame.draw.rect(s, b.color, r, border_radius=6)
            roof = pygame.Rect(r.left, r.top, r.width, 60)
            pygame.draw.rect(s, b.roof, roof, border_radius=6)
            for wx in range(r.left + 30, r.right - 50, 70):
                for wy in range(r.top + 90, r.bottom - 60, 80):
                    pygame.draw.rect(s, (250, 220, 120) if lit else (150, 190, 220), (wx, wy, 34, 34))
            pygame.draw.rect(s, (60, 40, 30), b.door.move(-ox, -oy))
            sign = f["md"].render(b.name, True, (255, 255, 255))
            s.blit(sign, sign.get_rect(center=roof.center))

    def draw_room(self, cam):
        s, f = self.screen, self.fonts
        ox, oy = cam
        room = ROOMS[self.room]
        s.fill((15, 12, 20))
        rw, rh = room.size
        area = pygame.Rect(-ox, -oy, rw, rh)
        pygame.draw.rect(s, room.floor, area)
        for fu in sorted(room.furniture, key=lambda fu: fu.solid):
            r = fu.rect.move(-ox, -oy)
            pygame.draw.rect(s, fu.color, r, border_radius=8)
            if fu.solid:
                pygame.draw.rect(s, (0, 0, 0), r, 2, border_radius=8)
            if fu.label:
                t = f["xs"].render(fu.label, True, (255, 255, 255))
                s.blit(t, t.get_rect(center=r.center))
        if self.room == "club":  # disco lights and dancers
            for i in range(6):
                a = self.ticks / 500 + i
                x = 610 + math.cos(a * 1.3) * 180 - ox
                y = 360 + math.sin(a) * 140 - oy
                glow = pygame.Surface((120, 120), pygame.SRCALPHA)
                col = [(255, 60, 160), (60, 200, 255), (255, 230, 60)][i % 3]
                pygame.draw.circle(glow, (*col, 70), (60, 60), 60)
                s.blit(glow, (x - 60, y - 60))
            for n in self.npcs:
                p = n.partner
                draw_person(s, (n.x - ox, n.y - oy), p.skin, p.hair, 1.3, self.ticks * 2, n.phase, n.outfit)
                t = f["xs"].render(p.name, True, TEXT)
                s.blit(t, t.get_rect(center=(n.x - ox, n.y - oy - 60)))
        if self.room == "apartments" and self.gs.date:
            p = self.gs.date
            draw_person(s, (520 - ox, 220 - oy), p.skin, p.hair, 1.4, self.ticks, 0, (200, 60, 90))
            t = f["sm"].render(p.name, True, TEXT)
            s.blit(t, t.get_rect(center=(520 - ox, 160 - oy)))
        pygame.draw.rect(s, (90, 75, 65), area, 18)
        mat = pygame.Rect(rw // 2 - 60 - ox, rh - 22 - oy, 120, 22)
        pygame.draw.rect(s, (160, 60, 60), mat)
        t = f["xs"].render("EXIT", True, (255, 255, 255))
        s.blit(t, t.get_rect(center=mat.center))

    def draw_player(self, cam):
        gs = self.gs
        keys = pygame.key.get_pressed()
        moving = any(keys[k] for k in MOVE_KEYS) and not self.phone_open
        hop = abs(math.sin(self.ticks / 90)) * 8 if moving else 0
        x, y = self.px - cam[0], self.py - cam[1]
        pygame.draw.ellipse(self.screen, (0, 0, 0), (x - 28, y - 8, 56, 16))
        draw_character(self.screen, gs.character, (x, y - 108 * SPRITE_SCALE - hop), SPRITE_SCALE,
                       gs.mood, gs.energy, gs.hygiene, gs.infection is not None, self.ticks, gs.piercings)

    def draw_hud(self):
        s, f, gs = self.screen, self.fonts, self.gs
        bar = pygame.Surface((W, 58), pygame.SRCALPHA)
        bar.fill((20, 16, 28, 220))
        s.blit(bar, (0, 0))
        s.blit(f["md"].render(f"Day {gs.day}/{GAME_LENGTH_DAYS} · {gs.time_name}", True, TEXT), (14, 8))
        where = "Town" if self.room == "town" else ROOMS[self.room].name
        s.blit(f["xs"].render(where, True, MUTED), (14, 34))
        for i, stat in enumerate(STAT_COLORS):
            x = 230 + i * 120
            val = getattr(gs, stat)
            s.blit(f["xs"].render(stat.capitalize(), True, MUTED), (x, 8))
            pygame.draw.rect(s, (50, 45, 60), (x, 28, 106, 14), border_radius=6)
            pygame.draw.rect(s, STAT_COLORS[stat] if val > 25 else BAD,
                             (x, 28, int(106 * val / 100), 14), border_radius=6)
        info = f["sm"].render(f"${gs.money}   Condoms {gs.condoms}   Charm {gs.charm}", True, GOOD)
        s.blit(info, info.get_rect(topright=(W - 14, 10)))
        hint = f["xs"].render("P: phone   1-5 / E: choose", True, MUTED)
        s.blit(hint, hint.get_rect(topright=(W - 14, 36)))
        sym = gs.symptoms()
        if sym:
            t = f["sm"].render("  ·  ".join(sym), True, BAD)
            r = t.get_rect(midtop=(W // 2, 66))
            pygame.draw.rect(s, (30, 20, 30), r.inflate(20, 8), border_radius=8)
            s.blit(t, r)

    def draw_diary(self):
        s, f = self.screen, self.fonts
        panel = pygame.Rect(14, H - 104, 640, 90)
        surf = pygame.Surface(panel.size, pygame.SRCALPHA)
        surf.fill((20, 16, 28, 200))
        s.blit(surf, panel)
        y = panel.bottom - 10
        for msg in reversed(self.gs.log):
            for line in reversed(wrap(msg, f["sm"], panel.width - 24)):
                y -= 22
                if y < panel.top + 6:
                    return
                col = TEXT if msg is self.gs.log[-1] else MUTED
                s.blit(f["sm"].render(line, True, col), (panel.left + 12, y))
            y -= 4

    def draw_popup(self, mouse):
        popup = self.active_popup()
        if not popup:
            return
        s, f = self.screen, self.fonts
        btns = self.popup_buttons(popup)
        t = f["md"].render(popup.title, True, ACCENT)
        r = t.get_rect(bottomleft=(btns[0].rect.left + 4, btns[0].rect.top - 8))
        bg = pygame.Rect(r.left - 12, r.top - 8, 404, btns[-1].rect.bottom - r.top + 16)
        pygame.draw.rect(s, (20, 16, 28), bg, border_radius=12)
        s.blit(t, r)
        for b, o in zip(btns, popup.options):
            b.draw(s, f, mouse, enabled=o.fn is not None)

    def draw_minimap(self):
        if self.room != "town":
            return
        k = 0.075
        mw, mh = int(TOWN_SIZE[0] * k), int(TOWN_SIZE[1] * k)
        mm = pygame.Rect(W - mw - 14, 100, mw, mh)
        pygame.draw.rect(self.screen, (40, 70, 40), mm)
        for r in ROADS:
            pygame.draw.rect(self.screen, ROAD, (mm.x + r.x * k, mm.y + r.y * k, r.w * k, r.h * k))
        for b in BUILDINGS:
            r = b.rect
            pygame.draw.rect(self.screen, b.roof, (mm.x + r.x * k, mm.y + r.y * k, r.w * k, r.h * k))
        pygame.draw.circle(self.screen, ACCENT, (int(mm.x + self.px * k), int(mm.y + self.py * k)), 4)
        pygame.draw.rect(self.screen, TEXT, mm, 1)

    def draw_night(self):
        if self.room != "town":
            return
        alpha = [0, 15, 70, 130][self.gs.slot]
        if alpha:
            o = pygame.Surface((W, H), pygame.SRCALPHA)
            o.fill((15, 15, 60, alpha))
            self.screen.blit(o, (0, 0))

    def draw_world(self, mouse):
        cam = self.camera()
        (self.draw_town if self.room == "town" else self.draw_room)(cam)
        self.draw_player(cam)
        self.draw_night()
        self.draw_hud()
        self.draw_minimap()
        self.draw_diary()
        if self.phone_open:
            self.draw_phone(mouse)
        else:
            self.draw_popup(mouse)

    def click_world(self, pos):
        if self.phone_open:
            return self.click_phone(pos)
        popup = self.active_popup()
        if popup:
            for i, b in enumerate(self.popup_buttons(popup)):
                if b.hit(pos):
                    return self.choose(i)

    def key_world(self, e):
        if e.key in (pygame.K_p, pygame.K_TAB):
            self.phone_open = not self.phone_open
            return
        if e.key == pygame.K_ESCAPE:
            self.phone_open, self.popup = False, None
            return
        if self.phone_open:
            if self.phone_tab == "swipe" and e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.do_swipe(e.key == pygame.K_RIGHT)
            return
        if pygame.K_1 <= e.key <= pygame.K_9:
            self.choose(e.key - pygame.K_1)
        elif e.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            popup = self.active_popup()
            if popup:
                for i, o in enumerate(popup.options):
                    if o.fn:
                        return self.choose(i)

    # ================================================================ phone
    def phone_buttons(self):
        P = self.PHONE
        btns = {
            "tab_swipe": Button((P.x + 20, P.y + 50, 155, 36), "Swipe", color=(60, 50, 75)),
            "tab_matches": Button((P.x + 185, P.y + 50, 155, 36), "Matches", color=(60, 50, 75)),
        }
        if self.phone_tab == "swipe":
            label = {"everyone": "Everyone", "vagina": "Women", "penis": "Men"}[self.gs.show_me]
            btns["filter"] = Button((P.x + 20, P.y + 96, 320, 30), f"Show me: {label}", color=(50, 44, 62))
            btns["nope"] = Button((P.x + 30, P.bottom - 70, 130, 52), "Nope", color=(120, 45, 45))
            btns["like"] = Button((P.right - 160, P.bottom - 70, 130, 52), "Like", color=(40, 110, 70))
        else:
            for i, p in enumerate(reversed(self.gs.matches)):
                btns[("text", i)] = Button((P.right - 110, P.y + 106 + i * 58, 90, 44), "Text",
                                           color=(120, 50, 85))
        return btns

    def draw_phone(self, mouse):
        s, f, gs, P = self.screen, self.fonts, self.gs, self.PHONE
        pygame.draw.rect(s, (12, 10, 16), P.inflate(16, 16), border_radius=36)
        pygame.draw.rect(s, (250, 245, 250), P, border_radius=28)
        t = f["md"].render("Spark", True, ACCENT)
        s.blit(t, t.get_rect(center=(P.centerx, P.y + 26)))
        btns = self.phone_buttons()
        for k, b in btns.items():
            if isinstance(k, str):
                b.draw(s, f, mouse, selected=k == f"tab_{self.phone_tab}")
        dark, soft = (40, 30, 50), (130, 110, 140)
        if self.phone_tab == "swipe":
            left = SWIPES_PER_DAY - gs.swipes_today
            if left <= 0:
                msg = f["md"].render("No swipes left today", True, soft)
                s.blit(msg, msg.get_rect(center=P.center))
                return
            if self.card is None:
                self.card = actions.new_profile(gs)
            p = self.card
            card = pygame.Rect(P.x + 30, P.y + 136, 300, 360).move(self.drag_x, 0)
            pygame.draw.rect(s, (255, 255, 255), card, border_radius=18)
            pygame.draw.rect(s, (220, 200, 220), card, 2, border_radius=18)
            photo = pygame.Rect(card.x + 14, card.y + 14, card.w - 28, 200)
            pygame.draw.rect(s, (230, 190, 210), photo, border_radius=12)
            s.set_clip(photo)
            draw_person(s, (photo.centerx, photo.centery + 40), p.skin, p.hair, 2.6, self.ticks, 0,
                        (200, 60, 90))
            s.set_clip(None)
            s.blit(f["lg"].render(f"{p.name}, {p.age}", True, dark), (card.x + 18, photo.bottom + 10))
            s.blit(f["sm"].render(f"{p.label} · {p.vibe}", True, soft), (card.x + 18, photo.bottom + 44))
            for i, line in enumerate(wrap(f"\"{p.bio}\"", f["sm"], card.w - 36)):
                s.blit(f["sm"].render(line, True, dark), (card.x + 18, photo.bottom + 72 + i * 22))
            if abs(self.drag_x) > 30:
                stamp = f["lg"].render("LIKE" if self.drag_x > 0 else "NOPE", True,
                                       GOOD if self.drag_x > 0 else BAD)
                s.blit(stamp, stamp.get_rect(center=(card.centerx, card.y + 40)))
            hint = f["xs"].render(f"Drag the card or use arrow keys · {left} swipes left", True, soft)
            s.blit(hint, hint.get_rect(center=(P.centerx, P.bottom - 86)))
        else:
            if not gs.matches:
                msg = f["sm"].render("No matches yet. Get swiping!", True, soft)
                s.blit(msg, msg.get_rect(center=P.center))
            for i, p in enumerate(reversed(gs.matches)):
                y = P.y + 106 + i * 58
                draw_person(s, (P.x + 44, y + 36), p.skin, p.hair, 0.9, 0, 0, (200, 60, 90))
                s.blit(f["md"].render(f"{p.name}, {p.age}", True, dark), (P.x + 76, y + 4))
                extra = f" · together {p.times}x" if p.times else ""
                s.blit(f["xs"].render(p.vibe + extra, True, soft), (P.x + 76, y + 26))
            for k, b in btns.items():
                if isinstance(k, tuple):
                    b.draw(s, f, mouse)

    def click_phone(self, pos):
        if not self.PHONE.collidepoint(pos):
            self.phone_open = False
            return
        for k, b in self.phone_buttons().items():
            if not b.hit(pos):
                continue
            if k == "tab_swipe":
                self.phone_tab = "swipe"
            elif k == "tab_matches":
                self.phone_tab = "matches"
            elif k in ("nope", "like"):
                self.do_swipe(k == "like")
            elif k == "filter":
                order = ["everyone", "vagina", "penis"]
                self.gs.show_me = order[(order.index(self.gs.show_me) + 1) % 3]
                self.card = None
            elif isinstance(k, tuple):
                p = list(reversed(self.gs.matches))[k[1]]
                actions.text_match(self.gs, p)
                self.phone_open = False
            return
        card = pygame.Rect(self.PHONE.x + 30, self.PHONE.y + 136, 300, 360)
        if self.phone_tab == "swipe" and card.collidepoint(pos):
            self.drag_start = pos[0]

    def do_swipe(self, right):
        if self.card is None:
            return
        res = actions.swipe(self.gs, self.card, right)
        if isinstance(res, str):
            self.show_toast(res)
        elif res:
            self.show_toast(f"It's a match with {self.card.name}!", GOOD)
        self.card, self.drag_x = None, 0

    # ================================================================= over
    def draw_over(self, mouse):
        gs, f = self.gs, self.fonts
        t = f["xl"].render("Game over", True, ACCENT)
        self.screen.blit(t, t.get_rect(center=(W // 2, 90)))
        r = f["md"].render(gs.end_reason, True, TEXT)
        self.screen.blit(r, r.get_rect(center=(W // 2, 145)))
        draw_character(self.screen, gs.character, (W // 2, 310), 0.9, gs.mood, gs.energy,
                       gs.hygiene, gs.infection is not None, self.ticks, gs.piercings)
        lines = [
            f"Days lived: {min(gs.day, GAME_LENGTH_DAYS)}",
            f"Hookups: {gs.total_hookups}  (with condom: {gs.protected_hookups})",
            f"Infections caught: {gs.infections_caught}   Piercings: {len(gs.piercings)}",
            f"Money left: ${gs.money}",
            f"SCORE: {gs.score()}",
        ]
        for i, line in enumerate(lines):
            s = f["md"].render(line, True, TEXT if i < 4 else GOOD)
            self.screen.blit(s, s.get_rect(center=(W // 2, 470 + i * 32)))
        Button((W // 2 - 100, 640, 200, 52), "Play again").draw(self.screen, f, mouse)

    def click_over(self, pos):
        if pygame.Rect(W // 2 - 100, 640, 200, 52).collidepoint(pos):
            self.char = Character(self.char.kind, self.char.name, self.char.body_color, self.char.hair_color)
            self.scene = "setup"

    # ================================================================= misc
    def show_toast(self, msg, color=BAD):
        self.toast, self.toast_color = msg, color
        self.toast_until = pygame.time.get_ticks() + 2500

    def draw_toast(self):
        if pygame.time.get_ticks() > self.toast_until:
            return
        s = self.fonts["md"].render(self.toast, True, TEXT)
        r = s.get_rect(center=(W // 2, 110))
        pygame.draw.rect(self.screen, self.toast_color, r.inflate(30, 16), border_radius=10)
        self.screen.blit(s, r)

    def drag_active(self):
        return self.scene == "world" and self.phone_open and self.drag_start is not None

    def frame(self, events, dt=1 / 60):
        self.ticks = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                getattr(self, f"click_{self.scene}")(e.pos)
            elif e.type == pygame.MOUSEMOTION and self.drag_active():
                self.drag_x = e.pos[0] - self.drag_start
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.drag_active():
                if abs(self.drag_x) > 100:
                    self.do_swipe(self.drag_x > 0)
                self.drag_start, self.drag_x = None, 0
            elif e.type == pygame.KEYDOWN and hasattr(self, f"key_{self.scene}"):
                getattr(self, f"key_{self.scene}")(e)
        if self.scene == "world":
            self.move(dt)
        self.screen.fill(BG)
        getattr(self, f"draw_{self.scene}")(mouse)
        self.draw_toast()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.frame(pygame.event.get(), min(dt, 0.05))
        pygame.quit()


def main():
    App().run()
