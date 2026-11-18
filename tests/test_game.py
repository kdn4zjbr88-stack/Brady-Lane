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


def test_pregnancy_is_hidden_then_shows_then_ends_game():
    gs = new_game()
    gs.rng.random = lambda: 0.0  # every roll hits
    actions.hook_up(gs, partner(), "inside")
    assert gs.conception is not None and not gs.symptoms()
    gs.money = 10_000
    while not any("late" in x for x in gs.symptoms()):
        actions.eat(gs)
        actions.shower(gs)
        actions.sleep(gs)
    actions.pregnancy_test(gs)
    assert gs.conception.revealed
    while not gs.game_over:
        actions.eat(gs)
        actions.shower(gs)
        actions.sleep(gs)
    assert "Baby" in gs.end_reason


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
