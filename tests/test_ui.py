import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from brady.ui import App  # noqa: E402
from brady.world import BUILDING_BY_KEY, ROOMS  # noqa: E402


def stand_on(app, key):
    spot = next(h for h in app.hotspots() if h.key == key)
    app.px, app.py = spot.zone.center


def test_walk_into_home_and_shower():
    app = App(seed=2)
    app.start_game()
    stand_on(app, "door:home")
    app.choose(0)
    assert app.room == "home"
    app.gs.hygiene = 10
    stand_on(app, "shower")
    app.choose(0)
    assert app.gs.hygiene > 90
    stand_on(app, "exit")
    app.choose(0)
    assert app.room == "town"
    app.frame([])


def test_walls_block_movement():
    app = App(seed=2)
    app.start_game()
    b = BUILDING_BY_KEY["home"]
    app.px, app.py = b.rect.centerx, b.rect.bottom + 15
    for _ in range(30):
        app.step(0, -1, 1 / 60)
    assert app.py > b.rect.bottom


def test_club_to_bedroom_flow():
    app = App(seed=5)
    app.start_game()
    gs = app.gs
    gs.slot = 2
    gs.rng.random = lambda: 0.0
    stand_on(app, "door:club")
    app.choose(0)
    assert app.room == "club" and app.npcs
    stand_on(app, "npc:0")
    app.choose(0)              # chat up -> match
    app.choose(0)              # go home with them
    assert app.room == "apartments" and gs.date
    stand_on(app, "bed")
    app.frame([])
    app.choose(1)              # no condom -> follow-up choice if pregnancy possible
    if app.popup:
        assert len(app.popup.options) == 2
        app.choose(0)
    assert gs.total_hookups == 1 and gs.date is None


def test_phone_swipe_and_render_everything():
    app = App(seed=3)
    app.start_game()
    app.phone_open = True
    app.frame([])
    app.gs.rng.random = lambda: 0.0
    app.do_swipe(True)
    assert app.gs.matches
    app.phone_tab = "matches"
    app.frame([])
    for room in ROOMS:
        app.warp(room)
        app.frame([])
