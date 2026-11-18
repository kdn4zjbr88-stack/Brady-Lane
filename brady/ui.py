"""Pygame front end for Brady."""
from __future__ import annotations

import random

import pygame

from . import actions
from .art import draw_character
from .model import (BODY_COLORS, CHARACTER_TYPES, GAME_LENGTH_DAYS, HAIR_COLORS,
                    Character, GameState)

W, H = 1100, 720
BG = (28, 24, 36)
PANEL = (44, 38, 56)
TEXT = (238, 232, 245)
MUTED = (160, 150, 175)
ACCENT = (232, 90, 140)
GOOD = (90, 200, 130)
BAD = (230, 80, 80)

STAT_COLORS = {
    "health": (230, 80, 90),
    "hygiene": (90, 170, 230),
    "energy": (240, 200, 70),
    "fullness": (240, 140, 60),
    "mood": (200, 110, 230),
}


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
    def __init__(self, seed=None):
        pygame.init()
        pygame.display.set_caption("Brady")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.fonts = {
            "xl": pygame.font.SysFont(None, 72),
            "lg": pygame.font.SysFont(None, 40),
            "md": pygame.font.SysFont(None, 28),
            "sm": pygame.font.SysFont(None, 24),
            "xs": pygame.font.SysFont(None, 20),
        }
        self.seed = seed
        self.char = Character()
        self.scene = "setup"
        self.gs: GameState | None = None
        self.toast, self.toast_until = "", 0
        self.running = True

    # ---------------------------------------------------------------- setup
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

    def draw_setup(self, mouse, ticks):
        f = self.fonts
        title = f["xl"].render("BRADY", True, ACCENT)
        self.screen.blit(title, title.get_rect(center=(W // 2, 50)))
        sub = f["sm"].render("Pick your character, then keep them healthy, happy and safe for "
                             f"{GAME_LENGTH_DAYS} days.", True, MUTED)
        self.screen.blit(sub, sub.get_rect(center=(W // 2, 95)))
        for key, b in self.setup_buttons().items():
            if key[0] == "kind":
                b.draw(self.screen, f, mouse, selected=self.char.kind == key[1])
                preview = Character(key[1], self.char.name, self.char.body_color, self.char.hair_color)
                draw_character(self.screen, preview, (b.rect.centerx, b.rect.centery - 5), 0.95,
                               ticks=ticks)
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

    def start_game(self):
        self.char.name = self.char.name.strip() or "Brady"
        self.gs = GameState(character=self.char, rng=random.Random(self.seed))
        self.gs.say(f"Welcome to life, {self.char.name}! Eat, stay clean, have fun, play safe.")
        self.scene = "play"

    # ----------------------------------------------------------------- play
    def play_buttons(self):
        btns, bw = {}, 126
        items = [(a.key, a.label, a.hint) for a in actions.ACTIONS]
        items.append(("hookup", "Hook up", "Pick a partner"))
        for i, (key, label, hint) in enumerate(items):
            btns[key] = Button((22 + i * (bw + 8), 630, bw, 62), label, hint)
        return btns

    def draw_play(self, mouse, ticks):
        gs, f = self.gs, self.fonts
        # top bar
        top = f["lg"].render(f"Day {gs.day}/{GAME_LENGTH_DAYS} · {gs.time_name}", True, TEXT)
        self.screen.blit(top, (24, 18))
        info = f["md"].render(f"${gs.money}    Condoms: {gs.condoms}", True, GOOD)
        self.screen.blit(info, info.get_rect(topright=(W - 24, 24)))

        # character panel
        panel = pygame.Rect(20, 64, 400, 550)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=14)
        draw_character(self.screen, gs.character, (panel.centerx, panel.centery - 10), 1.25,
                       gs.mood, gs.energy, gs.hygiene, gs.infection is not None, ticks)
        name = f["lg"].render(gs.character.name, True, TEXT)
        self.screen.blit(name, name.get_rect(center=(panel.centerx, panel.bottom - 30)))

        # stats
        sp = pygame.Rect(440, 64, 640, 210)
        pygame.draw.rect(self.screen, PANEL, sp, border_radius=14)
        for i, stat in enumerate(STAT_COLORS):
            y = sp.top + 20 + i * 36
            val = getattr(gs, stat)
            self.screen.blit(f["md"].render(stat.capitalize(), True, TEXT), (sp.left + 20, y))
            bar = pygame.Rect(sp.left + 140, y, 420, 20)
            pygame.draw.rect(self.screen, (30, 26, 40), bar, border_radius=8)
            fill = bar.copy()
            fill.width = int(bar.width * val / 100)
            pygame.draw.rect(self.screen, STAT_COLORS[stat] if val > 25 else BAD, fill, border_radius=8)
            self.screen.blit(f["sm"].render(f"{int(val)}", True, MUTED), (bar.right + 12, y + 1))
        status = []
        if gs.infection:
            status.append("Symptoms: itching & burning. See a doctor!")
        if gs.scare_days:
            status.append(f"Pregnancy scare: {gs.scare_days} day(s) of waiting")
        if status:
            s = f["sm"].render("  ·  ".join(status), True, BAD)
            self.screen.blit(s, (sp.left + 20, sp.bottom - 22))

        # log
        lp = pygame.Rect(440, 290, 640, 324)
        pygame.draw.rect(self.screen, PANEL, lp, border_radius=14)
        self.screen.blit(f["md"].render("Diary", True, ACCENT), (lp.left + 20, lp.top + 14))
        y = lp.bottom - 16
        for msg in reversed(gs.log):
            for line in reversed(wrap(msg, f["sm"], lp.width - 40)):
                y -= 24
                if y < lp.top + 44:
                    break
                self.screen.blit(f["sm"].render(line, True, TEXT if msg is gs.log[-1] else MUTED),
                                 (lp.left + 20, y))
            y -= 6
            if y < lp.top + 44:
                break

        for key, b in self.play_buttons().items():
            b.draw(self.screen, f, mouse)

    def click_play(self, pos):
        for key, b in self.play_buttons().items():
            if not b.hit(pos):
                continue
            if key == "hookup":
                err = actions.can_hook_up(self.gs)
                if err:
                    self.show_toast(err)
                else:
                    self.scene = "hookup"
                return
            act = next(a for a in actions.ACTIONS if a.key == key)
            err = act.func(self.gs)
            if err:
                self.show_toast(err)
            self.check_over()

    # --------------------------------------------------------------- hookup
    def hookup_buttons(self):
        btns = {}
        for i, p in enumerate(self.gs.partners):
            y = 170 + i * 72
            btns[("safe", i)] = Button((620, y, 180, 54), "Use a condom", f"{self.gs.condoms} left",
                                       color=(40, 100, 70))
            btns[("raw", i)] = Button((812, y, 180, 54), "No protection", "Risky!", color=(120, 45, 45))
        btns[("cancel",)] = Button((W // 2 - 90, 640, 180, 50), "Never mind")
        return btns

    def draw_hookup(self, mouse, ticks):
        f = self.fonts
        t = f["lg"].render("Who are you texting tonight?", True, TEXT)
        self.screen.blit(t, t.get_rect(center=(W // 2, 110)))
        for i, p in enumerate(self.gs.partners):
            y = 170 + i * 72
            row = pygame.Rect(100, y, 900, 54)
            pygame.draw.rect(self.screen, PANEL, row, border_radius=10)
            hearts = f"{max(1, round(p.chemistry * 5))}/5"
            line = f"{p.name}, {p.age} · {p.vibe}"
            if p.times:
                line += f" · together {p.times}x"
            self.screen.blit(f["md"].render(line, True, TEXT), (row.left + 18, y + 8))
            self.screen.blit(f["sm"].render(f"Chemistry {hearts}", True, ACCENT), (row.left + 18, y + 31))
        for key, b in self.hookup_buttons().items():
            enabled = not (key[0] == "safe" and self.gs.condoms <= 0)
            b.draw(self.screen, f, mouse, enabled=enabled)

    def click_hookup(self, pos):
        for key, b in self.hookup_buttons().items():
            if not b.hit(pos):
                continue
            if key[0] == "cancel":
                self.scene = "play"
                return
            if key[0] == "safe" and self.gs.condoms <= 0:
                self.show_toast("You're out of condoms. Buy some first.")
                return
            err = actions.hook_up(self.gs, self.gs.partners[key[1]], protected=key[0] == "safe")
            if err:
                self.show_toast(err)
            self.scene = "play"
            self.check_over()
            return

    # ----------------------------------------------------------------- over
    def draw_over(self, mouse, ticks):
        gs, f = self.gs, self.fonts
        t = f["xl"].render("Game over", True, ACCENT)
        self.screen.blit(t, t.get_rect(center=(W // 2, 90)))
        r = f["md"].render(gs.end_reason, True, TEXT)
        self.screen.blit(r, r.get_rect(center=(W // 2, 145)))
        draw_character(self.screen, gs.character, (W // 2, 310), 0.9, gs.mood, gs.energy,
                       gs.hygiene, gs.infection is not None, ticks)
        lines = [
            f"Days lived: {min(gs.day, GAME_LENGTH_DAYS)}",
            f"Hookups: {gs.total_hookups}  (protected: {gs.protected_hookups})",
            f"Infections caught: {gs.infections_caught}",
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

    # ----------------------------------------------------------------- misc
    def check_over(self):
        if self.gs.game_over:
            self.scene = "over"

    def show_toast(self, msg):
        self.toast, self.toast_until = msg, pygame.time.get_ticks() + 2500

    def draw_toast(self):
        if pygame.time.get_ticks() > self.toast_until:
            return
        s = self.fonts["md"].render(self.toast, True, TEXT)
        r = s.get_rect(center=(W // 2, 600))
        pygame.draw.rect(self.screen, BAD, r.inflate(30, 16), border_radius=10)
        self.screen.blit(s, r)

    def frame(self, events):
        mouse, ticks = pygame.mouse.get_pos(), pygame.time.get_ticks()
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                getattr(self, f"click_{self.scene}")(e.pos)
            elif e.type == pygame.KEYDOWN and self.scene == "setup":
                if e.key == pygame.K_BACKSPACE:
                    self.char.name = self.char.name[:-1]
                elif e.key == pygame.K_RETURN:
                    self.start_game()
                elif e.unicode.isprintable() and len(self.char.name) < 14:
                    self.char.name += e.unicode
        self.screen.fill(BG)
        getattr(self, f"draw_{self.scene}")(mouse, ticks)
        self.draw_toast()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.frame(pygame.event.get())
            self.clock.tick(60)
        pygame.quit()


def main():
    App().run()
