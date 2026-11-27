import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from brady import actions, events  # noqa: E402
from brady.ui import App  # noqa: E402
from brady.world import BUILDING_BY_KEY, ROOMS  # noqa: E402


def stand_on(app, key):
    spot = next(h for h in app.hotspots() if h.key == key)
    app.me.x, app.me.y = spot.zone.center


def new_app(seed=2):
    app = App(seed=seed)
    app.start_game()
    return app


def test_walk_into_home_and_shower():
    app = new_app()
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
    app = new_app()
    b = BUILDING_BY_KEY["home"]
    app.me.x, app.me.y = b.rect.centerx - 80, b.rect.bottom + 15
    for _ in range(30):
        app.step(0, -1, 1 / 60)
    assert app.me.y > b.rect.bottom


def test_club_to_bedroom_flow():
    app = new_app(5)
    gs = app.gs
    gs.slot = 2
    gs.rng.random = lambda: 0.0
    stand_on(app, "door:club")
    app.choose(0)
    assert app.room == "club" and app.goers
    stand_on(app, "goer:0")
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


def test_talk_to_npc_in_town():
    app = new_app()
    stand_on(app, "talk:granny")
    app.choose(0)                       # "Talk"
    assert app.popup and app.popup.text
    app.choose(0)                       # first reply
    assert app.popup is None and "Granny Muffin" in app.gs.log[-1]


def test_shopkeeper_chat_option():
    app = new_app()
    app.warp("pharmacy")
    stand_on(app, "pharmacy")
    popup = app.active_popup()
    assert popup.options[-1].label.startswith("Chat")


def test_delivery_opens_baby_setup_and_baby_follows():
    app = new_app()
    gs = app.gs
    actions.deliver(gs)
    app.frame([])
    assert app.scene == "baby_setup"
    app.draft.name = "Lulu"
    app.draft.accessory = "Bow"
    app.frame([])
    app.finish_baby()
    assert app.scene == "world" and gs.baby.name == "Lulu" and gs.baby.accessory == "Bow"
    app.me.x += 300
    for _ in range(60):
        app.follow_baby(1 / 60)
    assert abs(app.bb.x - app.me.x) < 80
    stand_on(app, "door:club")
    gs.slot = 2
    assert app.active_popup().options[0].fn is None   # no babies in the club
    app.baby_menu()
    assert app.popup.title == "Lulu"
    app.frame([])


def test_event_hotspot():
    app = new_app()
    events.spawn(app.gs, "puppy", 1100, 700)
    stand_on(app, "event:0")
    mood = app.gs.mood
    app.choose(0)
    assert app.gs.mood > mood


def test_phone_and_render_everything():
    app = new_app(3)
    app.phone_open = True
    app.frame([])
    app.gs.rng.random = lambda: 0.0
    app.do_swipe(True)
    assert app.gs.matches
    app.phone_tab = "matches"
    app.frame([])
    app.phone_open = False
    app.gs.raining = True
    app.gs.slot = 3
    for key in events.CATALOGUE:
        events.spawn(app.gs, key, 1100, 700)
    app.frame([])
    for room in ROOMS:
        app.warp(room)
        app.frame([])


def test_hardware_upgrade_appears_at_home():
    app = new_app()
    gs = app.gs
    gs.money = 1000
    app.warp("hardware")
    stand_on(app, "hardware")
    labels = [o.label for o in app.active_popup().options]
    app.choose(labels.index("Hot tub"))
    assert "hottub" in gs.upgrades
    app.warp("home")
    assert any(h.key == "hottub" for h in app.hotspots())
    assert not any(h.key == "gym" for h in app.hotspots())
    app.frame([])


def test_townsperson_date_at_your_place():
    app = new_app()
    gs = app.gs
    gs.slot = 2
    gs.affection["jaz"] = 80
    stand_on(app, "talk:jaz")
    app.choose(0)                                        # Talk
    labels = [o.label for o in app.popup.options]
    assert "Flirt" in labels and "Ask on a date" in labels and "Come over tonight?" in labels
    app.choose(labels.index("Come over tonight?"))
    assert gs.date.name == "Jaz" and gs.date_place == "home"
    assert not any(h.key == "talk:jaz" for h in app.hotspots())
    app.warp("home")
    app.frame([])
    stand_on(app, "sleep")
    assert app.active_popup().title.startswith("Get frisky with Jaz")
    app.choose(0)                                        # with a condom
    assert gs.total_hookups == 1 and gs.date is None


def test_stadium_and_batting_minigame():
    app = new_app()
    gs = app.gs
    gs.day, gs.slot = 3, 2
    app.warp("ballpark")
    app.frame([])
    stand_on(app, "plate")
    app.choose(0)
    assert app.scene == "batting" and app.ab.mode == "game"
    app.frame([])
    app.bat_phase, app.pitch_t = "pitch", 0.93
    app.ab.is_strike = True
    app.swing()
    assert app.ab.hits == ["homer"]
    app.frame([])
    app.end_batting()
    assert app.scene == "world" and gs.played_today and gs.team_wins + gs.team_losses == 1
    stand_on(app, "cage")
    app.choose(0)
    assert app.scene == "batting" and app.ab.mode == "practice"
    app.end_batting()


def test_phone_bills_and_cycle_apps():
    app = new_app()
    gs = app.gs
    gs.character.kind = "vagina"
    app.phone_open = True
    for tab in ("bills", "cycle", "swipe", "matches"):
        app.phone_tab = tab
        app.frame([])
    app.phone_tab = "bills"
    pay = app.phone_buttons()[("pay", "rent")]
    money = gs.money
    app.click_phone(pay.rect.center)
    assert gs.money == money - 140
    gs.phone_off = True
    app.phone_tab = "swipe"
    app.frame([])
    assert "nope" not in app.phone_buttons()


def test_job_options_at_diner():
    app = new_app()
    app.warp("diner")
    stand_on(app, "eat")
    labels = [o.label for o in app.active_popup().options]
    assert any(l.startswith("Apply: Line cook") for l in labels)
