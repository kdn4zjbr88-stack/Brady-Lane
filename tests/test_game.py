import random

from brady import actions
from brady.model import Character, GameState, Partner


def new_game(seed=1, kind="penis"):
    return GameState(character=Character(kind=kind), rng=random.Random(seed))


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


def test_party_only_in_evening_and_meets_people():
    gs = new_game()
    assert actions.party(gs) is not None
    gs.slot = 2
    assert actions.party(gs) is None
    assert gs.partners and all(p.age >= 18 for p in gs.partners)


def test_protected_hookup_uses_condom_and_needs_one():
    gs = new_game()
    p = Partner("Sam", 30, "Sweet", 1.0, 1.0)
    gs.partners.append(p)
    assert actions.hook_up(gs, p, protected=True) is None
    assert gs.condoms == 0 and gs.protected_hookups == 1
    assert actions.hook_up(gs, p, protected=True) is not None


def test_unprotected_with_risky_partner_infects_and_clinic_cures():
    gs = new_game()
    p = Partner("Sam", 30, "Wild", 1.0, 1.0)
    gs.partners.append(p)
    actions.hook_up(gs, p, protected=False)
    assert gs.infection is not None
    actions.clinic(gs)
    assert gs.infection is None


def test_starvation_ends_game():
    gs = new_game()
    gs.money = 0
    for _ in range(200):
        if gs.game_over:
            break
        actions.shower(gs)
    assert gs.game_over and gs.health <= 0


def test_surviving_all_days_ends_game():
    gs = new_game()
    gs.money = 10_000
    while not gs.game_over:
        actions.eat(gs)
        actions.shower(gs)
        actions.sleep(gs)
    assert "survived" in gs.end_reason
