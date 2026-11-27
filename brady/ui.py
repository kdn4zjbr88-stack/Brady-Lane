"""Pygame front end for Brady in Genitopia: setup, a walkable town, interiors, NPCs, phone and baby."""
from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass, field
from typing import Callable

import pygame

from . import actions, baseball, bills, cycle, events, jobs, npcs, scenery, upgrades
from .art import draw_baby, draw_character, shade
from .model import (BABY_ACCESSORIES, BODY_COLORS, CHARACTER_TYPES, GAME_LENGTH_DAYS, HAIR_COLORS,
                    ONESIE_COLORS, PIERCINGS, SWIPES_PER_DAY, TOWN_NAME, Character, GameState, Partner,
                    piercing_label)
from .world import BUILDING_BY_KEY, BUILDINGS, ROOMS, TOWN_SIZE, Hotspot, town_solids

W, H = 1100, 720
BG = (24, 20, 32)
PANEL = (48, 42, 62)
TEXT = (240, 234, 246)
MUTED = (165, 155, 182)
ACCENT = (236, 96, 146)
GOOD = (100, 205, 140)
BAD = (232, 86, 86)

STAT_COLORS = {
    "health": (232, 84, 96),
    "hygiene": (96, 172, 232),
    "energy": (242, 202, 76),
    "fullness": (242, 146, 66),
    "mood": (202, 116, 232),
}
SPEED = 300
SCALE = 0.42          # characters in the world
BABY_SCALE = 0.55
MOVE_KEYS = (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
             pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)


def F(size, bold=True):
    return scenery.font(size, bold)


class Button:
    def __init__(self, rect, label, sub="", color=PANEL, size=19):
        self.rect = pygame.Rect(rect)
        self.label, self.sub, self.color, self.size = label, sub, color, size

    def draw(self, surf, mouse, enabled=True, selected=False):
        hover = self.rect.collidepoint(mouse) and enabled
        col = ACCENT if selected else self.color
        if hover:
            col = shade(col, 1.15)
        if not enabled:
            col = (58, 54, 66)
        scenery.alpha_rect(surf, (0, 0, 0, 70), self.rect.move(0, 3), 12)
        scenery.grad(surf, self.rect, shade(col, 1.1), shade(col, 0.85), 12)
        fg = TEXT if enabled else MUTED
        lbl = F(self.size).render(self.label, True, fg)
        if self.sub:
            surf.blit(lbl, lbl.get_rect(center=(self.rect.centerx, self.rect.centery - 9)))
            sub = F(13, False).render(self.sub, True, shade(fg, 0.8))
            surf.blit(sub, sub.get_rect(center=(self.rect.centerx, self.rect.centery + 12)))
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
    text: str = ""


@dataclass
class ClubGoer:
    partner: Partner
    x: float
    y: float
    phase: float


@dataclass
class Walker:
    x: float = 0
    y: float = 0
    dist: float = 0
    moving: bool = False

    @property
    def frame(self):
        return int(self.dist / 16) % 4 if self.moving else -1


@dataclass
class BabyDraft:
    name: str = ""
    skin: str = "Brown"
    hair: str = "Black"
    onesie: str = "Sky"
    accessory: str = "None"
    extra: dict = field(default_factory=dict)


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


def panel(surf, rect, alpha=215, radius=16):
    rect = pygame.Rect(rect)
    scenery.alpha_rect(surf, (0, 0, 0, 60), rect.move(0, 4), radius)
    scenery.alpha_rect(surf, (22, 18, 30, alpha), rect, radius)


class App:
    PHONE = pygame.Rect(W - 400, 80, 360, 600)

    def __init__(self, seed=None):
        pygame.init()
        pygame.display.set_caption(f"Brady: {TOWN_NAME}")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.seed = seed
        self.char = Character()
        self.scene = "setup"
        self.gs: GameState | None = None
        self.toast, self.toast_color, self.toast_until = "", BAD, 0
        self.running = True
        self.ticks = 0
        self.drag_start: int | None = None
        self.drag_x = 0
        self.draft = BabyDraft()

    # ================================================================ setup
    def setup_buttons(self):
        btns = {}
        for i, kind in enumerate(CHARACTER_TYPES):
            btns[("kind", kind)] = Button((190 + i * 380, 120, 340, 350), "", color=(40, 34, 52))
        for i, name in enumerate(BODY_COLORS):
            btns[("body", name)] = Button((300 + i * 108, 492, 98, 38), name)
        for i, name in enumerate(HAIR_COLORS):
            btns[("hair", name)] = Button((300 + i * 108, 546, 98, 38), name)
        btns[("start",)] = Button((W // 2 - 120, 630, 240, 58), f"Move to {TOWN_NAME}", color=(150, 55, 100))
        return btns

    def backdrop(self):
        scenery.grad(self.screen, (0, 0, W, H), (46, 30, 62), (18, 14, 26))
        for i in range(5):
            scenery.alpha_ellipse(self.screen, (236, 96, 146, 14), (i * 260 - 100, 520 - (i % 2) * 60, 420, 300))

    def draw_setup(self, mouse):
        self.backdrop()
        t = F(54).render("BRADY", True, ACCENT)
        self.screen.blit(t, t.get_rect(center=(W // 2, 44)))
        sub = F(17, False).render(f"Life in {TOWN_NAME}. Keep your character healthy, happy and safe for "
                                  f"{GAME_LENGTH_DAYS} days. Adults only.", True, MUTED)
        self.screen.blit(sub, sub.get_rect(center=(W // 2, 88)))
        for key, b in self.setup_buttons().items():
            if key[0] == "kind":
                b.draw(self.screen, mouse, selected=self.char.kind == key[1])
                look = Character(key[1], self.char.name, self.char.body_color, self.char.hair_color)
                draw_character(self.screen, look, (b.rect.centerx, b.rect.bottom - 44), 0.86, ticks=self.ticks)
                lbl = F(20).render(key[1].capitalize(), True, TEXT)
                self.screen.blit(lbl, lbl.get_rect(center=(b.rect.centerx, b.rect.bottom - 20)))
            elif key[0] == "body":
                b.draw(self.screen, mouse, selected=self.char.body_color == key[1])
            elif key[0] == "hair":
                b.draw(self.screen, mouse, selected=self.char.hair_color == key[1])
            else:
                b.draw(self.screen, mouse)
        for y, txt in ((511, "Skin"), (565, "Hair")):
            t = F(18).render(txt, True, MUTED)
            self.screen.blit(t, t.get_rect(midright=(285, y)))
        name = F(18).render(f"Name: {self.char.name}_   (type to rename)", True, TEXT)
        self.screen.blit(name, name.get_rect(midleft=(30, 660)))

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
        self.gs.say(f"Welcome to {TOWN_NAME}, {self.char.name}! Walk with WASD/arrows, P for your phone.")
        self.room = "town"
        self.me = Walker(*BUILDING_BY_KEY["home"].outside_spot)
        self.bb = Walker(self.me.x - 40, self.me.y)
        self.goers: list[ClubGoer] = []
        self.popup: Popup | None = None
        self.phone_open = False
        self.phone_tab = "swipe"
        self.card: Partner | None = None
        self.scene = "world"

    # ================================================================ baby setup
    def baby_buttons(self):
        btns = {}
        rows = [("skin", list(BODY_COLORS)), ("hair", list(HAIR_COLORS)), ("onesie", list(ONESIE_COLORS)),
                ("accessory", list(BABY_ACCESSORIES))]
        for r, (field_, values) in enumerate(rows):
            for i, v in enumerate(values):
                btns[(field_, v)] = Button((470 + i * 112, 190 + r * 70, 104, 40), v)
        btns[("done",)] = Button((610, 600, 240, 56), "Welcome, baby!", color=(150, 55, 100))
        return btns

    def draw_baby_setup(self, mouse):
        self.backdrop()
        t = F(40).render("It's a baby!", True, ACCENT)
        self.screen.blit(t, t.get_rect(center=(W // 2, 50)))
        s = F(17, False).render("Make them yours. They'll follow you everywhere (except the club).", True, MUTED)
        self.screen.blit(s, s.get_rect(center=(W // 2, 92)))
        d = self.draft
        card = pygame.Rect(60, 140, 360, 460)
        panel(self.screen, card, 180, 24)
        preview = self.preview_baby()
        draw_baby(self.screen, preview, (card.centerx, card.bottom - 90), 2.6, self.ticks)
        nm = F(26).render(d.name or "(type a name)", True, TEXT if d.name else MUTED)
        self.screen.blit(nm, nm.get_rect(center=(card.centerx, card.bottom - 40)))
        for key, b in self.baby_buttons().items():
            if key[0] == "done":
                b.draw(self.screen, mouse, enabled=bool(d.name.strip()))
            else:
                b.draw(self.screen, mouse, selected=getattr(d, key[0]) == key[1])
        for r, label in enumerate(("Skin", "Hair", "Onesie", "Extra")):
            t = F(18).render(label, True, MUTED)
            self.screen.blit(t, t.get_rect(midright=(455, 210 + r * 70)))
        hint = F(16, False).render("Type the baby's name on your keyboard", True, MUTED)
        self.screen.blit(hint, hint.get_rect(midleft=(470, 500)))

    def preview_baby(self):
        from .model import Baby
        d = self.draft
        return Baby(name=d.name or "?", skin=d.skin, hair=d.hair, onesie=d.onesie, accessory=d.accessory)

    def click_baby_setup(self, pos):
        for key, b in self.baby_buttons().items():
            if b.hit(pos):
                if key[0] == "done":
                    self.finish_baby()
                else:
                    setattr(self.draft, key[0], key[1])

    def key_baby_setup(self, e):
        d = self.draft
        if e.key == pygame.K_BACKSPACE:
            d.name = d.name[:-1]
        elif e.key == pygame.K_RETURN:
            self.finish_baby()
        elif e.unicode and e.unicode.isprintable() and len(d.name) < 12:
            d.name += e.unicode

    def finish_baby(self):
        d, b = self.draft, self.gs.baby
        if not d.name.strip():
            return
        b.name, b.skin, b.hair, b.onesie, b.accessory = d.name.strip(), d.skin, d.hair, d.onesie, d.accessory
        self.gs.baby_needs_setup = False
        self.gs.say(f"Say hi to {b.name}! Press B any time to feed or cuddle them.")
        self.bb.x, self.bb.y = self.me.x - 40, self.me.y
        self.scene = "world"

    # ================================================================ world: geometry
    def room_size(self):
        return TOWN_SIZE if self.room == "town" else ROOMS[self.room].size

    def solids(self):
        return town_solids() if self.room == "town" else ROOMS[self.room].solids(self.gs.upgrades)

    def npc_pos(self, n: npcs.Npc):
        if not n.patrol:
            return n.pos
        pts = n.patrol + [n.patrol[0]]
        segs = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
        d = (self.ticks / 1000 * 55) % sum(segs)
        for (a, b), L in zip(zip(pts, pts[1:]), segs):
            if d <= L:
                t = d / L
                return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            d -= L
        return n.pos

    def hotspots(self) -> list[Hotspot]:
        if self.room == "town":
            spots = [Hotspot(f"event:{i}", pygame.Rect(e.x - 70, e.y - 60, 140, 110), e.title)
                     for i, e in enumerate(self.gs.events)]
            for n in npcs.npcs_in("town", self.gs):
                x, y = self.npc_pos(n)
                spots.append(Hotspot(f"talk:{n.key}", pygame.Rect(x - 55, y - 50, 110, 90), n.name))
            return spots + [Hotspot(f"door:{b.key}", b.door_zone, b.name) for b in BUILDINGS]
        spots = ROOMS[self.room].spots(self.gs.upgrades)
        spots = [Hotspot(f"talk:{n.key}", pygame.Rect(n.pos[0] - 55, n.pos[1] - 50, 110, 90), n.name)
                 for n in npcs.npcs_in(self.room, self.gs) if n.key == "coach"] + spots
        if self.room == "club":
            spots = [Hotspot(f"goer:{i}", pygame.Rect(g.x - 55, g.y - 55, 110, 110), g.partner.name)
                     for i, g in enumerate(self.goers)] + spots
        return spots

    def feet(self):
        return pygame.Rect(self.me.x - 16, self.me.y - 10, 32, 20)

    def move(self, dt):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if self.phone_open or not (dx or dy):
            self.me.moving = False
        else:
            self.step(dx, dy, dt)
        self.follow_baby(dt)

    def step(self, dx, dy, dt):
        norm = math.hypot(dx, dy)
        rw, rh = self.room_size()
        wall = 0 if self.room == "town" else 18
        top = 0 if self.room == "town" else 64
        solids = self.solids()
        x0, y0 = self.me.x, self.me.y
        for axis, d in (("x", dx), ("y", dy)):
            if not d:
                continue
            old = (self.me.x, self.me.y)
            if axis == "x":
                self.me.x = max(wall + 16, min(rw - wall - 16, self.me.x + d / norm * SPEED * dt))
            else:
                self.me.y = max(top + 20, min(rh - wall - 10, self.me.y + d / norm * SPEED * dt))
            if self.feet().collidelist(solids) != -1:
                self.me.x, self.me.y = old
        moved = math.hypot(self.me.x - x0, self.me.y - y0)
        self.me.dist += moved
        self.me.moving = moved > 0
        if self.popup and self.popup.anchor and not self.popup.anchor.collidepoint(self.me.x, self.me.y):
            self.popup = None

    def follow_baby(self, dt):
        if not self.gs.baby_with_you:
            return
        tx, ty = self.me.x - 38, self.me.y + 4
        d = math.hypot(tx - self.bb.x, ty - self.bb.y)
        if d > 30:
            step = min(d - 20, SPEED * 0.95 * dt)
            self.bb.x += (tx - self.bb.x) / d * step
            self.bb.y += (ty - self.bb.y) / d * step
            self.bb.dist += step
            self.bb.moving = True
        else:
            self.bb.moving = False

    def current_spot(self) -> Hotspot | None:
        for h in self.hotspots():
            if h.zone.collidepoint(self.me.x, self.me.y):
                return h
        return None

    def warp(self, room, pos=None):
        self.room = room
        self.popup = None
        self.me.x, self.me.y = pos if room == "town" else ROOMS[room].spawn
        self.bb.x, self.bb.y = self.me.x - 40, self.me.y + 4
        if room == "club":
            rng = self.gs.rng
            anat = None if self.gs.show_me == "everyone" else self.gs.show_me
            self.goers = [ClubGoer(Partner.random(rng, anat), rng.randint(460, 800), rng.randint(270, 500),
                                   rng.random() * 6) for _ in range(rng.randint(3, 4))]

    # ================================================================ choices
    def do(self, fn, *args, then=None):
        def run():
            err = fn(self.gs, *args)
            if err:
                self.show_toast(err)
            elif then:
                then()
            self.after_action()
        return run

    def after_action(self):
        if self.gs.game_over:
            self.scene = "over"
        elif self.gs.baby_needs_setup:
            b = self.gs.baby
            self.draft = BabyDraft(skin=b.skin, hair=b.hair)
            self.popup = None
            self.scene = "baby_setup"

    def talk(self, key):
        gs = self.gs
        n = npcs.NPC_BY_KEY[key]
        line = npcs.pick_line(gs, n)
        spot = self.current_spot()

        def answer(reply):
            def run():
                npcs.respond(gs, n, line, reply)
                self.popup = None
                self.after_action()
            return run

        def romance(fn):
            def run():
                self.popup = None
                self.do(fn, n)()
            return run

        opts = [Option(r.text, "", answer(r)) for r in line.replies]
        aff = npcs.affection(gs, n)
        opts.append(Option("Flirt", "Charm check" if not n.decline else "Worth a shot?", romance(npcs.flirt)))
        if not n.decline and aff >= 35:
            opts.append(Option("Ask on a date", "$25 · +Affection", romance(npcs.go_on_date)))
        if not n.decline and aff >= 65:
            opts.append(Option("Come over tonight?", "Meet at your place" if gs.is_night_time else "Ask in the evening",
                               romance(npcs.invite_home) if gs.is_night_time else None))
        status = "" if n.decline else f" · {npcs.stage(gs, n)} {aff}/100"
        self.popup = Popup(f"{n.name}{status}", opts, anchor=spot.zone if spot else None,
                           text=f"\"{npcs.say(line.text, gs)}\"")

    def chat_option(self, spot):
        if not spot.npc:
            return []
        n = npcs.NPC_BY_KEY[spot.npc]
        return [Option(f"Chat with {n.name.split()[-1]}", n.role, lambda: self.talk(n.key))]

    def job_options(self, place):
        gs = self.gs
        out = []
        for job in jobs.JOBS.values():
            if job.place != place:
                continue
            if gs.job == job.key:
                hours = "/".join(("Morn", "Aft", "Eve", "Night")[s] for s in job.slots)
                ok = gs.slot in job.slots
                out.append(Option(f"Work a shift (+${jobs.pay_for(gs)})", f"{job.title} · {hours}",
                                  self.do(jobs.work) if ok else None))
            else:
                need = f" · needs charm {job.min_charm}" if job.min_charm else ""
                out.append(Option(f"Apply: {job.title}", f"${job.pay}/shift · {job.perk}{need}",
                                  self.do(jobs.apply, job.key)))
        return out

    def frisky(self, p, place):
        gs, A = self.gs, actions
        n = gs.condoms

        def cuddle(g):
            g.say(f"You and {p.name} cuddle and talk till late. Cute.")
            g.adjust(mood=8)
            npc = npcs.npc_for(p.name)
            if npc:
                npcs.change_affection(g, npc, 6)
            g.date = None
            g.advance()

        opts = [Option("Use a condom", f"{n} left", self.do(A.hook_up, p, "condom") if n else None),
                Option("No condom", "Risky...", self.ask_finish)]
        if place == "home" and "hottub" in gs.upgrades:
            def tub(g):
                g.adjust(mood=18, energy=8)
                npc = npcs.npc_for(p.name)
                if npc:
                    npcs.change_affection(g, npc, 8)
                g.say(f"You and {p.name} soak in the hot tub. Bubbles. Candles. Wow.")
            opts.append(Option("Hot tub first", "Set the mood", self.do(tub)))
        opts.append(Option("Just cuddle", "Call it a night", self.do(cuddle)))
        return Popup(f"Get frisky with {p.name}?", opts)

    def options_for(self, spot: Hotspot) -> Popup | None:
        gs, key, A = self.gs, spot.key, actions
        if key.startswith("talk:"):
            n = npcs.NPC_BY_KEY[key[5:]]
            sub = n.role if n.decline else f"{n.role} · {npcs.stage(gs, n)}"
            return Popup(n.name, [Option("Talk", sub, lambda: self.talk(n.key))])
        if key.startswith("event:"):
            ev = gs.events[int(key[6:])]
            opts = [Option(o.label, o.sub, self.do(o.fn) if o.fn else None) for o in events.options(gs, ev)]
            return Popup(ev.title, opts, text=events.intro(ev))
        if key.startswith("door:"):
            b = BUILDING_BY_KEY[key[5:]]
            if b.key == "club" and not gs.is_night_time:
                return Popup(b.name, [Option("Closed", "Opens in the evening", None)])
            if b.key == "club" and gs.baby_with_you:
                return Popup(b.name, [Option("Bouncer: \"No babies!\"", "Leave the baby in the crib at home", None)])
            if b.key in ("office", "diner", "pharmacy", "studio", "hardware") and gs.time_name == "Night":
                return Popup(b.name, [Option("Closed", "Come back in the morning", None)])
            if b.key == "apartments" and not (gs.date and gs.date_place == "apartments"):
                return Popup(b.name, [Option("Locked", "Nobody's expecting you. Text a match.", None)])
            sub = ""
            if b.key == "apartments":
                sub = f"{gs.date.name} is waiting"
            elif b.key == "home" and gs.date and gs.date_place == "home":
                sub = f"{gs.date.name} is waiting in your bedroom"
            elif b.key == "clinic" and gs.in_labor:
                sub = "Labor! Hurry!"
            elif b.key == "ballpark":
                sub = f"Game tonight vs the {baseball.opponent(gs)}!" if baseball.is_game_day(gs) else f"Ballers {baseball.record(gs)}"
            return Popup(b.name, [Option("Go inside", sub, lambda: self.warp(b.key))])
        if key == "exit":
            b = BUILDING_BY_KEY[self.room]
            return Popup("Exit", [Option("Leave", f"Back to {TOWN_NAME}", lambda: self.warp("town", b.outside_spot))])
        simple = {
            "mirror": ("Mirror", "Check yourself out", "See your charm", A.mirror),
            "snack": ("Fridge", "Grab a snack", f"${A.SNACK_PRICE} · +20 fullness", A.snack),
            "shower": ("Bathroom", "Take a shower", "Hygiene to 100", A.shower),
            "pee": ("Bathroom", "Use the toilet", "", A.pee),
            "dance": ("Dance floor", "Dance", "+Mood, sweaty", A.dance),
            "cook": ("Chef's kitchen", "Cook a meal", "$4 · +45 fullness", upgrades.cook),
            "tv": ("Giant TV", "Watch TV", "Ballers games on game nights", upgrades.watch_tv),
            "gym": ("Home gym", "Work out", "+Fitness (charm), sweaty", upgrades.workout),
            "hottub": ("Hot tub", "Soak", "+Mood, +Energy", upgrades.hot_tub),
        }
        if key in simple:
            title, label, sub, fn = simple[key]
            return Popup(title, [Option(label, sub, self.do(fn))])
        if key == "sleep":
            if gs.date and gs.date_place == "home":
                return self.frisky(gs.date, "home")
            return Popup("Your bed", [Option("Sleep", "Skip to morning, full energy", self.do(A.sleep))])
        if key == "work":
            return Popup("Your desk", self.job_options("office"))
        if key == "bar":
            return Popup("Bar", [Option("Order a drink", f"${A.DRINK_PRICE} · +Mood", self.do(A.drink)),
                                 *self.job_options("club"), *self.chat_option(spot)])
        if key == "eat":
            opts = [Option("Burger meal", f"${A.MEAL_PRICE} · +45 fullness", self.do(A.eat))]
            if gs.craving:
                who = "you" if gs.is_carrier else gs.conception.partner if gs.conception else "you"
                opts.insert(0, Option(f"Craving: {gs.craving}", f"${A.MEAL_PRICE} · for {who}",
                                      self.do(A.satisfy_craving)))
            return Popup("Bean's Diner", opts + self.job_options("diner") + self.chat_option(spot))
        if key == "crib":
            b = gs.baby
            if not b:
                return Popup("Crib", [Option("An empty crib", "Waiting for a little one...", None)])
            label = f"Pick up {b.name}" if b.in_crib else f"Put {b.name} in the crib"
            sub = "They'll come with you" if b.in_crib else "Safe at home while you go out"
            return Popup("Crib", [Option(label, sub, self.do(A.crib_baby))])
        if key == "pharmacy":
            opts = [Option(f"Condoms x{A.CONDOM_PACK_SIZE}", f"${A.CONDOM_PACK_PRICE}", self.do(A.buy_condoms)),
                    Option("Pregnancy test", f"${A.TEST_PRICE}", self.do(A.pregnancy_test)),
                    Option("Morning-after pill", f"${A.PILL_PRICE} · best within a day", self.do(A.morning_after_pill)),
                    Option("Baby formula x2", f"${A.FORMULA_PRICE}", self.do(A.buy_formula))]
            if gs.character.kind == "vagina":
                opts += [Option("Pads & tampons x6", f"${A.SUPPLIES_PRICE} · you have {gs.period_supplies}",
                                self.do(A.buy_supplies)),
                         Option("Painkillers x3", f"${A.PAINKILLER_PRICE} · for cramps", self.do(A.buy_painkillers))]
            return Popup("Pharmacy", opts + self.job_options("pharmacy") + self.chat_option(spot))
        if key == "clinic":
            opts = []
            if gs.in_labor:
                opts.append(Option("Deliver the baby!", "Free at Genitopia General", self.do(A.deliver_at_clinic)))
            elif gs.conception and gs.conception.revealed and gs.is_carrier:
                opts.append(Option("Prenatal checkup", f"${A.CHECKUP_PRICE} · +Health", self.do(A.prenatal_checkup)))
            opts.append(Option("STI test & treatment", f"${A.CLINIC_PRICE}", self.do(A.clinic)))
            return Popup("Dr. Ova", opts + self.chat_option(spot))
        if key == "studio":
            return Popup("Piercings", [
                Option(piercing_label(n, gs.character.kind), f"${A.piercing_price(gs, n)} · +{c} charm",
                       self.do(A.get_piercing, n) if n not in gs.piercings else None)
                for n, (_, c) in PIERCINGS.items()] + self.job_options("studio") + self.chat_option(spot))
        if key == "hardware":
            return Popup("Screw & Nail: home upgrades", [
                Option(u.name, f"${u.price} · {u.blurb}" if u.key not in gs.upgrades else "Owned",
                       self.do(upgrades.buy, u.key) if u.key not in gs.upgrades else None)
                for u in upgrades.UPGRADES.values()] + self.chat_option(spot))
        if key == "plate":
            if baseball.game_on(gs) and not gs.played_today:
                return Popup("Home plate", [Option(f"Play tonight vs the {baseball.opponent(gs)}", "4 at-bats · SPACE to swing",
                                                   lambda: self.start_batting("game"))])
            nxt = baseball.next_game_day(gs)
            return Popup("Home plate", [Option("No game right now", f"Next game: day {nxt}, evening", None)])
        if key == "cage":
            return Popup("Batting cage", [Option("Batting practice", f"${baseball.PRACTICE} · 10 pitches",
                                                 lambda: self.start_batting("practice"))])
        if key == "bleachers":
            ok = baseball.game_on(gs) and not gs.played_today
            return Popup("Bleachers", [Option(f"Watch the game (${baseball.TICKET})",
                                              f"vs the {baseball.opponent(gs)}" if ok else "Games: evening every 3rd day",
                                              self.do(baseball.watch_game) if ok else None)])
        if key == "concession":
            def hotdog(g):
                if g.money < 6:
                    return "Hot dogs are $6."
                g.money -= 6
                g.adjust(fullness=30, mood=5)
                g.say("A ballpark hot dog. Mustard everywhere. Perfect.")
            return Popup("Concessions", [Option("Hot dog", "$6 · +30 fullness", self.do(hotdog)),
                                         *self.job_options("ballpark")])
        if key.startswith("goer:"):
            p = self.goers[int(key[5:])].partner
            title = f"{p.name}, {p.age} · {p.vibe}"
            if p in gs.matches:
                go = self.do(A.go_home_with, p, then=lambda: self.warp("apartments"))
                return Popup(title, [Option("Go home with them", "Things are heating up", go)])
            return Popup(title, [Option("Chat them up", f"Your charm: {gs.charm}", self.do(A.chat_up, p))])
        if key == "bed":
            p = gs.date
            if not p or gs.date_place != "apartments":
                return Popup("Their bed", [Option("Nobody here", "Time to head home", None)])
            return self.frisky(p, "apartments")
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

    def baby_menu(self):
        b = self.gs.baby
        if not b:
            return self.show_toast("You don't have a baby.")
        if b.in_crib:
            return self.show_toast(f"{b.name} is in the crib at home.")
        self.popup = Popup(f"{b.name}", [
            Option("Feed a bottle", f"{self.gs.formula} bottles left",
                   self.close_after(self.do(actions.feed_baby)) if self.gs.formula else None),
            Option("Cuddle", "+Baby happiness, +Mood", self.close_after(self.do(actions.cuddle_baby))),
        ], text=f"Fed {int(b.fullness)} · Happy {int(b.happiness)}" + ("  · CRYING" if b.crying else ""))

    def active_popup(self) -> Popup | None:
        if self.popup:
            return self.popup
        spot = self.current_spot()
        return self.options_for(spot) if spot else None

    def popup_layout(self, popup):
        x, w, h = W - 410, 390, 50
        lines = wrap(popup.text, F(16, False), w - 24) if popup.text else []
        top = H - 18 - len(popup.options) * (h + 8)
        btns = [Button((x, top + i * (h + 8), w, h), f"{i + 1}. {o.label}", o.sub, color=(70, 58, 88))
                for i, o in enumerate(popup.options)]
        text_top = top - 10 - len(lines) * 20
        return btns, lines, text_top

    def choose(self, i):
        popup = self.active_popup()
        if popup and 0 <= i < len(popup.options) and popup.options[i].fn:
            popup.options[i].fn()

    # ================================================================ world: drawing
    def camera(self):
        rw, rh = self.room_size()
        cx = (rw - W) / 2 if rw <= W else max(0, min(rw - W, self.me.x - W / 2))
        cy = (rh - H) / 2 - 20 if rh <= H else max(0, min(rh - H, self.me.y - H / 2))
        return int(cx), int(cy)

    def draw_world(self, mouse):
        cam = self.camera()
        ox, oy = cam
        s, gs = self.screen, self.gs
        if self.room == "town":
            bg = scenery.town_surface()
            occluders = scenery.town_occluders()
        else:
            room = ROOMS[self.room]
            bg = scenery.room_surface(room, gs.upgrades if self.room == "home" else ())
            occluders = scenery.room_occluders(room)
            s.fill((12, 10, 16))
        s.blit(bg, (0, 0), pygame.Rect(ox, oy, W, H)) if self.room == "town" else s.blit(bg, (-ox, -oy))
        if self.room == "club":
            scenery.dance_floor(s, ROOMS["club"].furniture[0].rect.move(-ox, -oy), self.ticks)

        drawables = []  # (sort_y, fn)
        view = pygame.Rect(ox - 200, oy - 200, W + 400, H + 400)

        def person(look, x, y, frame=-1, scale=SCALE, **kw):
            if view.collidepoint(x, y):
                drawables.append((y, lambda: draw_character(s, look, (x - ox, y - oy), scale, ticks=self.ticks,
                                                            frame=frame, **kw)))

        person(gs.character, self.me.x, self.me.y, self.me.frame, mood=gs.mood, energy=gs.energy,
               hygiene=gs.hygiene, infected=gs.infection is not None, piercings=gs.piercings, belly=gs.belly_stage)
        b = gs.baby
        if b and not gs.baby_needs_setup:
            if not b.in_crib:
                drawables.append((self.bb.y, lambda: draw_baby(s, b, (self.bb.x - ox, self.bb.y - oy), BABY_SCALE,
                                                               self.ticks, self.bb.frame)))
            elif self.room == "home":
                drawables.append((150, lambda: draw_baby(s, b, (360 - ox, 128 - oy), BABY_SCALE * 0.9, self.ticks)))
        if self.room == "home" and gs.date and gs.date_place == "home":
            npc = npcs.npc_for(gs.date.name)
            look = npc.look if npc else gs.date.look
            person(look, 340, 300)
            drawables.append((301, lambda: self.name_tag(gs.date.name, 340 - ox, 300 - oy - 132)))
        if self.room == "ballpark":
            drawables.append((0, lambda: self.draw_scoreboard(ox, oy)))
        for n in npcs.npcs_in(self.room, gs):
            x, y = self.npc_pos(n)
            frame = int(self.ticks / 120) % 4 if n.patrol else -1
            person(n.look, x, y, frame)
            drawables.append((y + 1, lambda x=x, y=y, n=n: self.name_tag(n.name, x - ox, y - oy - 132)))
        if self.room == "town":
            for ev in gs.events:
                if view.collidepoint(ev.x, ev.y):
                    drawables.append((ev.y, lambda ev=ev: scenery.draw_event(s, ev, (ev.x - ox, ev.y - oy),
                                                                             self.ticks, SCALE)))
        if self.room == "club":
            for g in self.goers:
                f = int(self.ticks / 140 + g.phase) % 4
                person(g.partner.look, g.x, g.y, f)
                drawables.append((g.y + 1, lambda g=g: self.name_tag(g.partner.name, g.x - ox, g.y - oy - 132)))
        if self.room == "apartments" and gs.date:
            person(gs.date.look, 520, 250)
            drawables.append((251, lambda: self.name_tag(gs.date.name, 520 - ox, 250 - oy - 132)))
        for sort_y, rect in occluders:
            if view.colliderect(rect):
                drawables.append((sort_y, lambda r=rect: s.blit(bg, (r.x - ox, r.y - oy), r)))
        for _, fn in sorted(drawables, key=lambda d: d[0]):
            fn()

        if self.room == "town":
            scenery.town_lights(s, cam, gs.slot, self.ticks)
            if gs.raining:
                scenery.rain(s, self.ticks)
        elif self.room == "club":
            scenery.club_lights(s, cam, self.ticks)
        self.draw_hud()
        self.draw_minimap()
        self.draw_diary()
        if self.phone_open:
            self.draw_phone(mouse)
        else:
            self.draw_popup(mouse)

    def draw_scoreboard(self, ox, oy):
        gs = self.gs
        r = pygame.Rect(560 - ox, 4 - oy, 280, 56)
        t1 = F(16).render(f"BALLERS  {baseball.record(gs)}", True, (255, 210, 90))
        nxt = f"TONIGHT vs {baseball.opponent(gs).upper()}" if baseball.is_game_day(gs) else f"NEXT GAME: DAY {baseball.next_game_day(gs)}"
        t2 = F(11).render(nxt, True, (250, 250, 250))
        self.screen.blit(t1, t1.get_rect(center=(r.centerx, r.y + 18)))
        self.screen.blit(t2, t2.get_rect(center=(r.centerx, r.y + 40)))

    def name_tag(self, name, x, y):
        t = F(13).render(name, True, (255, 255, 255))
        r = t.get_rect(center=(x, y))
        scenery.alpha_rect(self.screen, (0, 0, 0, 120), r.inflate(12, 6), 8)
        self.screen.blit(t, r)

    def draw_hud(self):
        s, gs = self.screen, self.gs
        panel(s, (8, 8, W - 16, 56), 200, 14)
        s.blit(F(16).render(f"Day {gs.day}/{GAME_LENGTH_DAYS} · {gs.weekday[:3]} · {gs.time_name}", True, TEXT), (22, 17))
        where = TOWN_NAME if self.room == "town" else ROOMS[self.room].name
        if gs.raining and self.room == "town":
            where += " · raining"
        s.blit(F(13, False).render(where, True, MUTED), (22, 40))
        for i, stat in enumerate(STAT_COLORS):
            x = 252 + i * 110
            val = getattr(gs, stat)
            s.blit(F(12, False).render(stat.capitalize(), True, MUTED), (x, 16))
            scenery.alpha_rect(s, (255, 255, 255, 25), (x, 34, 98, 12), 6)
            col = STAT_COLORS[stat] if val > 25 else BAD
            if val > 1:
                scenery.grad(s, (x, 34, max(12, int(98 * val / 100)), 12), shade(col, 1.15), shade(col, 0.85), 6)
        info = F(16).render(f"${gs.money}  ·  Condoms {gs.condoms}  ·  Charm {gs.charm}", True, GOOD)
        s.blit(info, info.get_rect(topright=(W - 22, 16)))
        hint = "P phone · B baby · 1-5 choose" if gs.baby else "P phone · 1-5 / E choose"
        h = F(12, False).render(hint, True, MUTED)
        s.blit(h, h.get_rect(topright=(W - 22, 40)))
        sym = gs.symptoms()
        due = bills.due_soon(gs)
        if due:
            late = any(b.overdue(gs) for b in due)
            sym = sym + [("BILLS OVERDUE (phone)" if late else "Bills due soon (phone)")]
        if sym:
            t = F(15).render("  ·  ".join(sym), True, (255, 200, 200))
            r = t.get_rect(midtop=(W // 2, 72))
            scenery.alpha_rect(s, (120, 30, 40, 200), r.inflate(24, 10), 10)
            s.blit(t, r)

    def draw_diary(self):
        s = self.screen
        box = pygame.Rect(12, H - 108, 640, 96)
        panel(s, box, 185, 14)
        y = box.bottom - 10
        f = F(15, False)
        for msg in reversed(self.gs.log):
            for line in reversed(wrap(msg, f, box.width - 28)):
                y -= 20
                if y < box.top + 6:
                    return
                col = TEXT if msg is self.gs.log[-1] else MUTED
                s.blit(f.render(line, True, col), (box.left + 14, y))
            y -= 4

    def draw_popup(self, mouse):
        popup = self.active_popup()
        if not popup:
            return
        s = self.screen
        btns, lines, text_top = self.popup_layout(popup)
        title = F(18).render(popup.title, True, ACCENT)
        title_y = text_top - 26
        bg = pygame.Rect(btns[0].rect.left - 10, title_y - 10, 410, btns[-1].rect.bottom - title_y + 20)
        panel(s, bg, 225, 16)
        s.blit(title, (bg.left + 14, title_y))
        for i, line in enumerate(lines):
            s.blit(F(16, False).render(line, True, TEXT), (bg.left + 14, text_top + i * 20))
        for b, o in zip(btns, popup.options):
            b.draw(s, mouse, enabled=o.fn is not None)

    def draw_minimap(self):
        if self.room != "town":
            return
        k = 0.072
        mw, mh = int(TOWN_SIZE[0] * k), int(TOWN_SIZE[1] * k)
        mm = pygame.Rect(W - mw - 16, 76, mw, mh)
        small = scenery._cache.get("minimap")
        if small is None:
            small = scenery._cache["minimap"] = pygame.transform.smoothscale(scenery.town_surface(), (mw, mh))
        panel(self.screen, mm.inflate(10, 10), 200, 10)
        self.screen.blit(small, mm)
        for ev in self.gs.events:
            pygame.draw.circle(self.screen, (255, 220, 90), (mm.x + ev.x * k, mm.y + ev.y * k), 3)
        pygame.draw.circle(self.screen, (255, 255, 255), (mm.x + self.me.x * k, mm.y + self.me.y * k), 5)
        pygame.draw.circle(self.screen, ACCENT, (mm.x + self.me.x * k, mm.y + self.me.y * k), 4)

    def click_world(self, pos):
        if self.phone_open:
            return self.click_phone(pos)
        popup = self.active_popup()
        if popup:
            for i, b in enumerate(self.popup_layout(popup)[0]):
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
            if self.phone_tab == "swipe" and not self.gs.phone_off and e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.do_swipe(e.key == pygame.K_RIGHT)
            return
        if e.key == pygame.K_b:
            if self.popup and self.gs.baby and self.popup.title == self.gs.baby.name:
                self.popup = None
            else:
                self.baby_menu()
        elif pygame.K_1 <= e.key <= pygame.K_9:
            self.choose(e.key - pygame.K_1)
        elif e.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            popup = self.active_popup()
            if popup:
                for i, o in enumerate(popup.options):
                    if o.fn:
                        return self.choose(i)

    # ================================================================ phone
    def phone_tabs(self):
        tabs = [("swipe", "Spark"), ("matches", "Matches"), ("bills", "Bills")]
        if self.gs.character.kind == "vagina":
            tabs.append(("cycle", "Cycle"))
        return tabs

    def phone_buttons(self):
        P, gs = self.PHONE, self.gs
        tabs = self.phone_tabs()
        tw = (320 - 8 * (len(tabs) - 1)) / len(tabs)
        btns = {f"tab_{k}": Button((P.x + 20 + i * (tw + 8), P.y + 52, tw, 34), label, color=(70, 60, 88),
                                   size=19 if len(tabs) < 4 else 15)
                for i, (k, label) in enumerate(tabs)}
        blocked = gs.phone_off and self.phone_tab in ("swipe", "matches")
        if self.phone_tab == "swipe" and not blocked:
            label = {"everyone": "Everyone", "vagina": "Women", "penis": "Men"}[gs.show_me]
            btns["filter"] = Button((P.x + 20, P.y + 94, 320, 28), f"Show me: {label}", color=(60, 52, 76))
            btns["nope"] = Button((P.x + 30, P.bottom - 70, 130, 50), "Nope", color=(170, 60, 70))
            btns["like"] = Button((P.right - 160, P.bottom - 70, 130, 50), "Like", color=(60, 160, 100))
        elif self.phone_tab == "matches" and not blocked:
            for i, p in enumerate(reversed(gs.matches)):
                btns[("text", i)] = Button((P.right - 104, P.y + 104 + i * 60, 84, 42), "Text", color=(160, 60, 105))
        elif self.phone_tab == "bills":
            for i, b in enumerate(gs.bills):
                btns[("pay", b.key)] = Button((P.right - 104, P.y + 112 + i * 70, 84, 44), "Pay", color=(60, 160, 100))
        return btns

    def draw_phone(self, mouse):
        s, gs, P = self.screen, self.gs, self.PHONE
        scenery.alpha_rect(s, (0, 0, 0, 90), P.inflate(24, 24).move(0, 8), 40)
        scenery.grad(s, P.inflate(16, 16), (40, 36, 46), (14, 12, 18), 38)
        scenery.grad(s, P, (252, 246, 250), (238, 230, 240), 30)
        title = dict(self.phone_tabs()).get(self.phone_tab, "Phone")
        t = F(22).render(title if self.phone_tab != "matches" else "Spark", True, ACCENT)
        s.blit(t, t.get_rect(center=(P.centerx, P.y + 28)))
        btns = self.phone_buttons()
        for k, b in btns.items():
            if isinstance(k, str) and k.startswith("tab_"):
                b.draw(s, mouse, selected=k == f"tab_{self.phone_tab}")
            elif isinstance(k, str):
                b.draw(s, mouse)
        dark, soft = (40, 30, 50), (130, 110, 140)
        if gs.phone_off and self.phone_tab in ("swipe", "matches"):
            for i, line in enumerate(["Service suspended.", "Pay your phone bill", "in the Bills app."]):
                m = F(18 if i == 0 else 15, i == 0).render(line, True, BAD if i == 0 else soft)
                s.blit(m, m.get_rect(center=(P.centerx, P.centery - 20 + i * 26)))
            return
        if self.phone_tab == "swipe":
            left = SWIPES_PER_DAY - gs.swipes_today
            if left <= 0:
                msg = F(20).render("No swipes left today", True, soft)
                s.blit(msg, msg.get_rect(center=P.center))
                return
            if self.card is None:
                self.card = actions.new_profile(gs)
            p = self.card
            card = pygame.Rect(P.x + 30, P.y + 134, 300, 362).move(self.drag_x, 0)
            scenery.alpha_rect(s, (0, 0, 0, 40), card.move(0, 6), 20)
            pygame.draw.rect(s, (255, 255, 255), card, border_radius=20)
            photo = pygame.Rect(card.x + 12, card.y + 12, card.w - 24, 206)
            scenery.grad(s, photo, (255, 210, 225), (220, 170, 210), 14)
            s.set_clip(photo)
            draw_character(s, p.look, (photo.centerx, photo.bottom + 26), 0.68, ticks=self.ticks, shadow=False)
            s.set_clip(None)
            s.blit(F(26).render(f"{p.name}, {p.age}", True, dark), (card.x + 18, photo.bottom + 10))
            s.blit(F(15, False).render(f"{p.label} · {p.vibe}", True, soft), (card.x + 18, photo.bottom + 44))
            for i, line in enumerate(wrap(f"\"{p.bio}\"", F(15, False), card.w - 36)):
                s.blit(F(15, False).render(line, True, dark), (card.x + 18, photo.bottom + 70 + i * 20))
            if abs(self.drag_x) > 30:
                stamp = F(30).render("LIKE" if self.drag_x > 0 else "NOPE", True, GOOD if self.drag_x > 0 else BAD)
                s.blit(stamp, stamp.get_rect(center=(card.centerx, card.y + 40)))
            hint = F(12, False).render(f"Drag the card or use arrow keys · {left} swipes left", True, soft)
            s.blit(hint, hint.get_rect(center=(P.centerx, P.bottom - 86)))
        elif self.phone_tab == "matches":
            if not gs.matches:
                msg = F(16, False).render("No matches yet. Get swiping!", True, soft)
                s.blit(msg, msg.get_rect(center=P.center))
            for i, p in enumerate(reversed(gs.matches)):
                y = P.y + 104 + i * 60
                clip = pygame.Rect(P.x + 18, y, 50, 50)
                pygame.draw.ellipse(s, (240, 215, 230), clip)
                s.set_clip(clip)
                draw_character(s, p.look, (clip.centerx, clip.bottom + 52), 0.3, shadow=False, bob=False)
                s.set_clip(None)
                s.blit(F(18).render(f"{p.name}, {p.age}", True, dark), (P.x + 78, y + 6))
                extra = f" · together {p.times}x" if p.times else ""
                s.blit(F(13, False).render(p.vibe + extra, True, soft), (P.x + 78, y + 28))
            for k, b in btns.items():
                if isinstance(k, tuple):
                    b.draw(s, mouse)
        elif self.phone_tab == "bills":
            for i, b in enumerate(gs.bills):
                y = P.y + 104 + i * 70
                row = pygame.Rect(P.x + 16, y, 328, 60)
                scenery.alpha_rect(s, (255, 255, 255, 200), row, 12)
                s.blit(F(17).render(f"{b.name}  ${b.amount(gs)}", True, dark), (row.x + 12, row.y + 8))
                over, days = b.overdue(gs), b.due_day - gs.day
                txt, col = ((f"OVERDUE by {over} day{'s' * (over > 1)}", BAD) if over else
                            ("Due today", (210, 140, 40)) if days == 0 else (f"Due day {b.due_day} (in {days})", soft))
                s.blit(F(13, over > 0).render(txt, True, col), (row.x + 12, row.y + 34))
            for k, b in btns.items():
                if isinstance(k, tuple):
                    b.draw(s, mouse)
            y = P.y + 330
            job = jobs.JOBS[gs.job] if gs.job else None
            lines = [
                ("Wallet", f"${gs.money}"),
                ("Job", f"{job.title} · ${jobs.pay_for(gs)}/shift" if job else "Unemployed"),
                ("Shifts worked", f"{gs.shifts} (raise every {jobs.RAISE_EVERY})" if job else "-"),
                ("Home upgrades", f"{len(gs.upgrades)} of {len(upgrades.UPGRADES)}"),
                ("Ballers", f"{baseball.record(gs)} · next game day {baseball.next_game_day(gs)}"),
            ]
            for i, (a, v) in enumerate(lines):
                s.blit(F(13, False).render(a, True, soft), (P.x + 24, y + i * 40))
                s.blit(F(16).render(v, True, dark), (P.x + 24, y + 16 + i * 40))
        elif self.phone_tab == "cycle":
            self.draw_cycle_app(P, dark, soft)

    def draw_cycle_app(self, P, dark, soft):
        s, gs = self.screen, self.gs
        if gs.conception:
            for i, line in enumerate(["Cycle paused", "You're pregnant!" if gs.visibly_pregnant else "Your period is late...",
                                      "Tracking resumes after the baby."]):
                m = F(18 if i == 0 else 15, i == 0).render(line, True, ACCENT if i == 0 else soft)
                s.blit(m, m.get_rect(center=(P.centerx, P.y + 200 + i * 28)))
            return
        w = 30
        x0 = P.x + (P.w - (w + 2) * cycle.CYCLE_LEN) // 2
        y = P.y + 112
        for d in range(1, cycle.CYCLE_LEN + 1):
            name, col = cycle.PHASE_INFO[cycle.PHASES[d]]
            r = pygame.Rect(x0 + (d - 1) * (w + 2), y, w, 46)
            scenery.grad(s, r, shade(col, 1.1), shade(col, 0.85), 6)
            if d == gs.cycle_day:
                pygame.draw.rect(s, dark, r.inflate(6, 6), 3, border_radius=8)
            t = F(12).render(str(d), True, (255, 255, 255))
            s.blit(t, t.get_rect(center=r.center))
        phase = cycle.phase(gs)
        name, col = cycle.PHASE_INFO[phase]
        s.blit(F(24).render(name, True, col), (P.x + 24, P.y + 182))
        s.blit(F(14, False).render(f"Day {gs.cycle_day} of {cycle.CYCLE_LEN}", True, soft), (P.x + 24, P.y + 214))
        until = cycle.days_until_period(gs)
        tips = {
            "period": "Cramps likely. Painkillers help. Pads/tampons get used up each time slot.",
            "follicular": "Energy's coming back. Good days ahead.",
            "fertile": "Fertile window: unprotected sex is MUCH riskier. You're glowing, though (+charm).",
            "luteal": "Winding down. Pregnancy risk is low (not zero!).",
            "pms": "Moody and snacky. Chocolate helps. Period soon.",
        }
        for i, line in enumerate(wrap(tips[phase], F(15, False), 300)):
            s.blit(F(15, False).render(line, True, dark), (P.x + 24, P.y + 248 + i * 20))
        rows = [("Next period", "now" if phase == "period" else f"in {until} day{'s' * (until != 1)}"),
                ("Pads & tampons", str(gs.period_supplies)),
                ("Painkillers", str(gs.painkillers)),
                ("Pregnancy risk today", {"period": "Low", "follicular": "Medium", "fertile": "HIGH",
                                          "luteal": "Low", "pms": "Low"}[phase])]
        for i, (a, v) in enumerate(rows):
            yy = P.y + 360 + i * 44
            s.blit(F(13, False).render(a, True, soft), (P.x + 24, yy))
            s.blit(F(17).render(v, True, BAD if v == "HIGH" or (a != "Next period" and v == "0") else dark),
                   (P.x + 24, yy + 16))

    def click_phone(self, pos):
        if not self.PHONE.collidepoint(pos):
            self.phone_open = False
            return
        for k, b in self.phone_buttons().items():
            if not b.hit(pos):
                continue
            if isinstance(k, str) and k.startswith("tab_"):
                self.phone_tab = k[4:]
            elif k in ("nope", "like"):
                self.do_swipe(k == "like")
            elif k == "filter":
                order = ["everyone", "vagina", "penis"]
                self.gs.show_me = order[(order.index(self.gs.show_me) + 1) % 3]
                self.card = None
            elif isinstance(k, tuple) and k[0] == "text":
                p = list(reversed(self.gs.matches))[k[1]]
                actions.text_match(self.gs, p)
                self.phone_open = False
            elif isinstance(k, tuple) and k[0] == "pay":
                err = bills.pay(self.gs, k[1])
                if err:
                    self.show_toast(err)
                else:
                    self.show_toast("Paid!", GOOD)
            return
        card = pygame.Rect(self.PHONE.x + 30, self.PHONE.y + 134, 300, 362)
        if self.phone_tab == "swipe" and card.collidepoint(pos) and not self.gs.phone_off:
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

    # ================================================================ batting mini-game
    PLATE = (550, 640)
    RELEASE = (550, 300)

    def start_batting(self, mode):
        gs = self.gs
        if mode == "practice":
            if gs.money < baseball.PRACTICE:
                return self.show_toast(f"Batting practice costs ${baseball.PRACTICE}.")
            if gs.energy < 15:
                return self.show_toast("Too tired to swing a bat.")
            gs.money -= baseball.PRACTICE
            self.ab = baseball.AtBat("practice")
        else:
            if not baseball.game_on(gs) or gs.played_today:
                return self.show_toast("No game right now.")
            self.ab = baseball.AtBat("game")
        self.ab.new_pitch(gs.rng)
        self.popup = None
        self.bat_phase, self.bat_t0, self.pitch_t, self.swing_t0 = "windup", pygame.time.get_ticks(), 0.0, None
        self.hit_anim = None
        self.scene = "batting"

    def update_batting(self):
        ab, now = self.ab, pygame.time.get_ticks()
        if self.bat_phase == "windup" and now - self.bat_t0 > 900:
            self.bat_phase, self.bat_t0 = "pitch", now
        elif self.bat_phase == "pitch":
            self.pitch_t = (now - self.bat_t0) / 1000 / baseball.PITCHES[ab.pitch]
            if self.pitch_t > 1.12:
                baseball.resolve(ab, "taken")
                self.bat_phase, self.result_until = "result", now + 1300
        elif self.bat_phase == "result" and now > self.result_until:
            if ab.done:
                return self.end_batting()
            ab.new_pitch(self.gs.rng)
            self.bat_phase, self.bat_t0, self.pitch_t, self.swing_t0, self.hit_anim = "windup", now, 0.0, None, None

    def swing(self):
        now = pygame.time.get_ticks()
        if self.swing_t0 and now - self.swing_t0 < 250:
            return
        self.swing_t0 = now
        if self.bat_phase != "pitch" or self.ab.swung:
            return
        ab = self.ab
        ab.swung = True
        outcome = baseball.judge_swing(ab, self.pitch_t)
        baseball.resolve(ab, outcome)
        if outcome in ("homer", "double", "single", "foul"):
            spread = {"homer": 0, "double": 140, "single": 260, "foul": 520}[outcome]
            self.hit_anim = (outcome, now, self.gs.rng.choice((-1, 1)) * self.gs.rng.uniform(0.3, 1) * spread,
                             self.ball_pos(self.pitch_t))
        self.bat_phase, self.result_until = "result", now + 1500

    def end_batting(self):
        gs, ab = self.gs, self.ab
        if ab.mode == "game":
            ab.at_bats_left = 0
        baseball.finish(gs, ab)
        self.scene = "world"
        self.toast_until = 0
        self.after_action()

    def ball_pos(self, t):
        ab = self.ab
        (x0, y0), (x1, y1) = self.RELEASE, self.PLATE
        t = max(0.0, t)
        x = x0 + (x1 - x0) * t
        if ab.pitch == "Curveball":
            x += math.sin(math.pi * min(t, 1)) * 70
        if not ab.is_strike:
            x += (110 if (hash(ab.pitch) + ab.strikes + ab.balls) % 2 else -110) * t ** 2
        y = y0 + (y1 - 50 - y0) * t ** 1.15
        return x, y

    def batting_bg(self):
        key = ("batting_bg", self.ab.mode)
        bg = scenery._cache.get(key)
        if bg is None:
            bg = pygame.Surface((W, H))
            night = self.ab.mode == "game"
            scenery.grad(bg, (0, 0, W, 170), (40, 30, 80) if night else (120, 180, 235),
                         (230, 120, 110) if night else (200, 225, 245))
            rng = random.Random(5)
            for row in range(5):                         # crowd in the stands
                y = 70 + row * 18
                scenery.grad(bg, (0, y, W, 18), (120, 125, 140), (90, 95, 110))
                for x in range(0, W, 9):
                    c = rng.choice([(240, 200, 160), (120, 80, 50), (200, 60, 80), (60, 110, 200), (250, 250, 250), (250, 210, 80)])
                    pygame.draw.circle(bg, c, (x + rng.randint(-2, 2), y + 6), 4)
            scenery.grad(bg, (0, 160, W, 40), (40, 100, 60), (30, 80, 50))
            for i, ad in enumerate(["GENITOPIA", "BEAN'S DINER", "WRAP IT UP!", "SCREW & NAIL", "CLUB VELVET"]):
                t = scenery.font(14).render(ad, True, (240, 240, 220))
                bg.blit(t, t.get_rect(center=(110 + i * 220, 180)))
            scenery.grad(bg, (0, 200, W, H - 200), (90, 160, 80), (60, 130, 60))
            for i in range(-10, 12):                     # mowing stripes in perspective
                pts = [(550 + i * 30, 200), (550 + (i + 0.5) * 30, 200), (550 + (i + 0.5) * 160, H), (550 + i * 160, H)]
                tmp = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.polygon(tmp, (255, 255, 255, 12), pts)
                bg.blit(tmp, (0, 0))
            pygame.draw.polygon(bg, (195, 145, 95), [(550, 250), (900, 470), (550, 720), (200, 470)])
            pygame.draw.polygon(bg, (85, 155, 80), [(550, 330), (780, 470), (550, 600), (320, 470)])
            pygame.draw.ellipse(bg, (185, 135, 88), (500, 280, 100, 40))
            for x, y in ((900, 470), (550, 250), (200, 470)):
                pygame.draw.rect(bg, (250, 250, 250), (x - 9, y - 6, 18, 12), border_radius=2)
            pygame.draw.ellipse(bg, (185, 135, 88), (430, 600, 240, 80))
            px, py = self.PLATE
            pygame.draw.polygon(bg, (250, 250, 250), [(px - 22, py - 8), (px + 22, py - 8), (px + 22, py + 2), (px, py + 12), (px - 22, py + 2)])
            scenery._cache[key] = bg
        return bg

    def draw_bat(self, pivot, angle):
        s = self.screen
        for i in range(26):
            k = i / 25
            r = 5 + 6 * k ** 1.6
            x = pivot[0] + math.cos(angle) * 150 * k
            y = pivot[1] + math.sin(angle) * 150 * k
            pygame.draw.circle(s, shade((200, 150, 90), 0.85 + 0.25 * k), (x, y), r)
        pygame.draw.circle(s, (60, 60, 70), pivot, 7)

    def draw_batting(self, mouse):
        s, gs, ab, now = self.screen, self.gs, self.ab, pygame.time.get_ticks()
        s.blit(self.batting_bg(), (0, 0))
        if ab.mode == "practice":                       # pitching machine
            scenery.grad(s, (515, 262, 70, 46), (120, 125, 135), (80, 85, 95), 10)
            pygame.draw.circle(s, (40, 40, 46), (550, 284), 16)
            pygame.draw.circle(s, (180, 185, 195), (550, 284), 6)
        else:
            lean = 6 if self.bat_phase == "windup" and (now - self.bat_t0) > 500 else 0
            draw_character(s, Character("penis", "Pitcher", "Tan", "Black", "cap"), (550 + lean, 318), 0.36,
                           ticks=self.ticks)
        if self.bat_phase == "pitch" or (self.bat_phase == "result" and not self.hit_anim and self.pitch_t < 1.25):
            t = min(self.pitch_t, 1.2)
            x, y = self.ball_pos(t)
            r = 3 + 10 * t
            scenery.alpha_ellipse(s, (0, 0, 0, 60), (x - r, self.PLATE[1] - 50 + (y - 300) * 0.1 + 40 * t, r * 2, r * 0.7))
            scenery.ball(s, (250, 250, 245), (x, y), r, light=1.0, dark=0.8, steps=6)
            pygame.draw.arc(s, (200, 40, 40), (x - r * 0.8, y - r * 0.8, r * 1.6, r * 1.6), 0.3, 1.8, max(1, int(r / 5)))
        if self.hit_anim:
            outcome, t0, dx, (hx, hy) = self.hit_anim
            k = min(1.0, (now - t0) / 900)
            x = hx + dx * k
            y = hy - (hy - (40 if outcome == "homer" else 220)) * k - math.sin(math.pi * k) * 120
            r = max(2, 13 * (1 - k * 0.85))
            scenery.ball(s, (250, 250, 245), (x, y), r, light=1.0, dark=0.8, steps=5)
        zone = pygame.Rect(self.PLATE[0] - 60, self.PLATE[1] - 150, 120, 110)
        scenery.alpha_rect(s, (255, 255, 255, 18), zone, 6)
        draw_character(s, gs.character, (400, 715), 0.95, gs.mood, gs.energy, gs.hygiene, ticks=self.ticks,
                       piercings=gs.piercings, belly=gs.belly_stage)
        pivot = (452, 560)
        swing_k = min(1.0, (now - self.swing_t0) / 160) if self.swing_t0 else 0
        self.draw_bat(pivot, -2.2 + swing_k * 2.9)
        box = pygame.Rect(16, 16, 330, 132)
        panel(s, box, 200, 14)
        title = "Batting practice" if ab.mode == "practice" else f"Ballers vs {baseball.opponent(gs)}"
        s.blit(F(18).render(title, True, ACCENT), (box.x + 14, box.y + 10))
        left = f"Pitches left: {ab.pitches_left}" if ab.mode == "practice" else f"At-bats left: {ab.at_bats_left}"
        s.blit(F(16).render(f"Balls {ab.balls} · Strikes {ab.strikes}", True, TEXT), (box.x + 14, box.y + 40))
        s.blit(F(16).render(left, True, TEXT), (box.x + 14, box.y + 64))
        hits = ", ".join(ab.hits) if ab.hits else "no hits yet"
        s.blit(F(14, False).render(f"Hits: {hits}", True, MUTED), (box.x + 14, box.y + 92))
        if self.bat_phase in ("pitch", "result"):
            t = F(18).render(ab.pitch + ("" if ab.is_strike else " (outside)"), True, (255, 255, 255))
            s.blit(t, t.get_rect(center=(550, 240)))
        if self.bat_phase == "result" and ab.result:
            good = any(w in ab.result for w in ("HOME", "Double", "hit", "base"))
            t = F(44).render(ab.result, True, (255, 220, 90) if good else (255, 255, 255))
            r = t.get_rect(center=(W // 2, 360))
            scenery.alpha_rect(s, (0, 0, 0, 120), r.inflate(40, 20), 14)
            s.blit(t, r)
        hint = F(15, False).render("SPACE or click to swing · time it as the ball reaches you · Esc to leave", True, TEXT)
        hr = hint.get_rect(center=(W // 2, H - 22))
        scenery.alpha_rect(s, (0, 0, 0, 120), hr.inflate(24, 10), 10)
        s.blit(hint, hr)

    def key_batting(self, e):
        if e.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.swing()
        elif e.key == pygame.K_ESCAPE:
            self.end_batting()

    def click_batting(self, pos):
        self.swing()

    # ================================================================= over
    def draw_over(self, mouse):
        gs = self.gs
        self.backdrop()
        t = F(52).render("Game over", True, ACCENT)
        self.screen.blit(t, t.get_rect(center=(W // 2, 70)))
        r = F(20, False).render(gs.end_reason, True, TEXT)
        self.screen.blit(r, r.get_rect(center=(W // 2, 118)))
        draw_character(self.screen, gs.character, (W // 2 - (40 if gs.baby else 0), 420), 0.8, gs.mood, gs.energy,
                       gs.hygiene, gs.infection is not None, self.ticks, gs.piercings, gs.belly_stage)
        if gs.baby:
            draw_baby(self.screen, gs.baby, (W // 2 + 90, 420), 1.0, self.ticks)
        lines = [
            f"Days lived: {min(gs.day, GAME_LENGTH_DAYS)}",
            f"Hookups: {gs.total_hookups}  (with condom: {gs.protected_hookups})",
            f"Infections caught: {gs.infections_caught}   Piercings: {len(gs.piercings)}",
            f"Baby: {gs.baby.name}" if gs.baby else "No kids (yet)",
            f"SCORE: {gs.score()}",
        ]
        for i, line in enumerate(lines):
            surf = F(19, i == 4).render(line, True, TEXT if i < 4 else GOOD)
            self.screen.blit(surf, surf.get_rect(center=(W // 2, 470 + i * 30)))
        Button((W // 2 - 100, 640, 200, 52), "Play again", color=(150, 55, 100)).draw(self.screen, mouse)

    def click_over(self, pos):
        if pygame.Rect(W // 2 - 100, 640, 200, 52).collidepoint(pos):
            self.char = Character(self.char.kind, self.char.name, self.char.body_color, self.char.hair_color)
            self.scene = "setup"

    # ================================================================= misc
    def show_toast(self, msg, color=BAD):
        self.toast, self.toast_color = msg, color
        self.toast_until = pygame.time.get_ticks() + 2600

    def draw_toast(self):
        if pygame.time.get_ticks() > self.toast_until:
            return
        t = F(18).render(self.toast, True, (255, 255, 255))
        r = t.get_rect(center=(W // 2, 112))
        scenery.alpha_rect(self.screen, (0, 0, 0, 80), r.inflate(34, 20).move(0, 3), 12)
        scenery.grad(self.screen, r.inflate(34, 20), shade(self.toast_color, 1.1), shade(self.toast_color, 0.85), 12)
        self.screen.blit(t, r)

    def drag_active(self):
        return self.scene == "world" and self.phone_open and self.drag_start is not None

    def frame(self, events_, dt=1 / 60):
        self.ticks = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        for e in events_:
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
            self.after_action()
        elif self.scene == "batting":
            self.update_batting()
        self.screen.fill(BG)
        getattr(self, f"draw_{self.scene}")(mouse)
        self.draw_toast()
        pygame.display.flip()

    async def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.frame(pygame.event.get(), min(dt, 0.05))
            await asyncio.sleep(0)  # lets the browser build breathe each frame
        pygame.quit()


def main():
    asyncio.run(App().run())
