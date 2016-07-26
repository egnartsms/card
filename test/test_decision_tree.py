import pytest

import gcxt
import decision_tree
from decision_tree import build_tree, cardset_relation, node_estimate
from common import Card


@pytest.fixture(scope='function')
def set_trump(monkeypatch):
    return lambda trump: monkeypatch.setattr(gcxt, 'trump', trump)


def test_i_put_rival_wins(set_trump):
    set_trump('hearts')
    node = build_tree([Card('clubs', 10), Card('diamonds', 8)],
                      [Card('hearts', 6)],
                      True)
    assert node_estimate(node) == 0.0


def test_i_put_result_draw(set_trump):
    set_trump('hearts')
    node = build_tree([Card('clubs', 10)],
                      [Card('clubs', 11)],
                      True)
    assert node_estimate(node) == 0.5
    node = build_tree([Card('clubs', 14)],
                      [Card('hearts', 6)],
                      True)
    assert node_estimate(node) == 0.5


def test_i_put_i_win(set_trump, monkeypatch):
    set_trump('hearts')
    monkeypatch.setattr(decision_tree, 'MAXDEPTH', 4)
    node = build_tree([Card('clubs', 10)],
                      [Card('clubs', 9)],
                      True)
    assert node_estimate(node) == 1.0
    node = build_tree([Card('clubs', 6), Card('clubs', 8), Card('clubs', 9),
                       Card('hearts', 8)],
                      [Card('clubs', 7)],
                      True)
    assert node_estimate(node) == 1.0


def test_rival_puts_i_win(set_trump):
    set_trump('hearts')
    node = build_tree([Card('clubs', 10)],
                      [Card('clubs', 9), Card('clubs', 6)],
                      False)
    assert node_estimate(node) == 1.0


def test_rival_puts_result_draw(set_trump):
    set_trump('hearts')
    node = build_tree([Card('clubs', 10)], [Card('clubs', 9)], False)
    assert node_estimate(node) == 0.5


def test_rival_puts_rival_wins(set_trump):
    set_trump('hearts')
    node = build_tree([Card('spades', 10)],
                      [Card('clubs', 9)],
                      False)
    assert node_estimate(node) == 0.0
    node = build_tree([Card('clubs', 6), Card('clubs', 8), Card('clubs', 9),
                       Card('hearts', 8)],
                      [Card('clubs', 7)],
                      False)
    assert node_estimate(node) == 0.0


def test_cardset_relation(set_trump):
    set_trump('spades')
    p1, p2 = cardset_relation(
        [Card('hearts', 10)],
        [Card('hearts', 9)]
    )
    assert p1 == 1.0 and p2 == 0.0

    p1, p2 = cardset_relation(
        [Card('hearts', 14), Card('hearts', 12)],
        [Card('diamonds', 8)]
    )
    assert p1 == 1.0 and p2 == 0.0

    p1, p2 = cardset_relation(
        [Card('hearts', 14), Card('hearts', 12)],
        [Card('diamonds', 13), Card('diamonds', 11)]
    )
    assert p1 == 0.75 and p2 == 0.25

    p1, p2 = cardset_relation(
        [Card('hearts', 14), Card('hearts', 12)],
        [Card('diamonds', 13)]
    )
    assert p1 == 0.5 and p2 == 0.5
