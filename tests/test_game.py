import random

from brady import actions
from brady.model import Character, GameState, Partner


def new_game(seed=1, kind="penis"):
    return GameState(character=Character(kind=kind), rng=random.Random(seed))


def partner(anatomy="vagina", sti=0.0):
    return Partner("Sam", 30, anatomy, "Sweet", "bio", 1.0, sti)


def test_actions_advance_time_and_roll_days():
    gs = new_game()
    for _ in range(4):
        actions.shower(gs)
    assert gs.day == 2 and gs.slot == 0


def test_sleep_restores_energy_and_moves_to_morning():
    gs = new_game()
    gs.energy = 10
    actions.sleep(gs)
    assert gs.day == 2 and gs.slot == 0 and gs.energy == 100


def test_condom_hookup_uses_condom_and_needs_one():
    gs = new_game()
    p = partner()
    assert actions.hook_up(gs, p, "condom") is None
    assert gs.condoms == 0 and gs.protected_hookups == 1
    assert actions.hook_up(gs, p, "condom") is not None


def test_unprotected_with_risky_partner_infects_and_clinic_cures():
    gs = new_game()
    actions.hook_up(gs, partner(sti=1.0), "inside")
    assert gs.infection is not None
    actions.clinic(gs)
    assert gs.infection is None


def live_days(gs, until):
    gs.money = 10_000
    gs.formula = 99
    while not until() and not gs.game_over:
        actions.eat(gs)
        actions.shower(gs)
        if gs.baby:
            actions.feed_baby(gs)
            actions.cuddle_baby(gs)
        actions.sleep(gs)


def test_pregnancy_shows_then_labor_then_baby():
    gs = new_game(kind="vagina")
    gs.rng.random = lambda: 0.0  # every roll hits
    actions.hook_up(gs, partner("penis"), "inside")
    assert gs.conception is not None and gs.belly_stage == 0
    assert not any("regnant" in x for x in gs.symptoms())
    live_days(gs, lambda: gs.visibly_pregnant)
    assert gs.belly_stage >= 1 and any("Pregnant" in x for x in gs.symptoms())
    live_days(gs, lambda: gs.in_labor)
    assert gs.in_labor and not gs.game_over
    assert actions.deliver_at_clinic(gs) is None
    assert gs.baby is not None and gs.baby_needs_setup and gs.conception is None


def test_cravings_are_satisfied_at_diner():
    gs = new_game(kind="vagina")
    gs.rng.random = lambda: 0.0
    actions.hook_up(gs, partner("penis"), "inside")
    live_days(gs, lambda: gs.craving is not None)
    assert gs.craving
    actions.satisfy_craving(gs)
    assert gs.craving is None


def test_missed_labor_still_delivers():
    gs = new_game()
    gs.rng.random = lambda: 0.0
    actions.hook_up(gs, partner("vagina"), "inside")
    live_days(gs, lambda: gs.baby is not None)
    assert gs.baby is not None and not gs.in_labor


def test_baby_needs_care_and_crib():
    gs = new_game()
    actions.deliver(gs)
    b = gs.baby
    b.fullness = b.happiness = 10
    gs.advance()
    assert b.crying
    assert actions.feed_baby(gs) is None and actions.cuddle_baby(gs) is None
    assert not b.crying
    actions.crib_baby(gs)
    assert b.in_crib and not gs.baby_with_you
    assert actions.feed_baby(gs) is not None


def test_no_drinking_while_pregnant():
    gs = new_game(kind="vagina")
    gs.rng.random = lambda: 0.0
    actions.hook_up(gs, partner("penis"), "inside")
    live_days(gs, lambda: gs.visibly_pregnant)
    assert actions.drink(gs) is not None


def test_no_pregnancy_with_same_anatomy():
    gs = new_game()
    gs.rng.random = lambda: 0.0
    actions.hook_up(gs, partner("penis"), "inside")
    assert gs.conception is None


def test_morning_after_pill_works_early():
    gs = new_game(kind="vagina")
    gs.rng.random = lambda: 0.0
    actions.hook_up(gs, partner("penis"), "inside")
    actions.morning_after_pill(gs)
    assert gs.conception is None


def test_piercings_cost_money_and_raise_charm():
    gs = new_game()
    before = gs.charm
    assert actions.get_piercing(gs, "Lip") is None
    assert gs.money == 90 and "Lip" in gs.piercings and gs.charm > before - 5
    assert actions.get_piercing(gs, "Lip") is not None


def test_swipe_limit_and_matching():
    gs = new_game()
    gs.rng.random = lambda: 0.0
    assert actions.swipe(gs, actions.new_profile(gs), True) is True
    assert len(gs.matches) == 1
    gs.swipes_today = 99
    assert isinstance(actions.swipe(gs, actions.new_profile(gs), True), str)


def test_dating_filter():
    gs = new_game()
    gs.show_me = "penis"
    assert all(actions.new_profile(gs).anatomy == "penis" for _ in range(20))


def test_text_match_only_sets_date_at_night():
    gs = new_game()
    p = partner()
    actions.text_match(gs, p)
    assert gs.date is None
    gs.slot = 2
    actions.text_match(gs, p)
    assert gs.date is p


def test_starvation_ends_game():
    gs = new_game()
    gs.money = 0
    while not gs.game_over:
        actions.shower(gs)
    assert gs.health <= 0


def test_surviving_all_days_ends_game():
    gs = new_game()
    gs.money = 10_000
    while not gs.game_over:
        actions.eat(gs)
        actions.shower(gs)
        actions.sleep(gs)
    assert "survived" in gs.end_reason


def test_events_and_flash_sale():
    from brady import events
    gs = new_game()
    assert actions.piercing_price(gs, "Lip") == 60
    events.spawn(gs, "flashsale")
    assert actions.piercing_price(gs, "Lip") == 30
    ev = events.spawn(gs, "wallet", 700, 920)
    turn_in = events.options(gs, ev)[0]
    turn_in.fn(gs)
    assert ev not in gs.events and gs.money == 170


def test_events_spawn_over_time():
    gs = new_game(seed=3)
    gs.money = 10_000
    seen = set()
    for _ in range(40):
        actions.shower(gs)
        seen |= {e.key for e in gs.events}
        actions.eat(gs)
    assert len(seen) >= 3


def test_npc_dialogue():
    from brady import npcs
    gs = new_game()
    granny = npcs.NPC_BY_KEY["granny"]
    line = npcs.pick_line(gs, granny)
    npcs.respond(gs, granny, line, line.replies[1])
    assert gs.talks["granny"] == 1 and "Granny" in gs.log[-1]
    gs.hygiene = 10
    assert "smell" in npcs.pick_line(gs, npcs.NPC_BY_KEY["officer"]).text
