"""
Implementation of a smart player.

Smart player remembers all the cards and tries to determine which cards has
the opponent. This information is used for decision making.
"""
import functools

import gcxt
from common import deckset, card_value, NCARDS_DECK_BEGINNING, NCARDS_PLAYER,\
    beats, factorial
from decision_tree import build_tree


class SmartPlayer:
    def __init__(self, cards):
        assert len(cards) == NCARDS_PLAYER
        self.cards = set(cards)
        self.blackset = set(deckset - self.cards)
        self.rivalcards = set()
        self.nrival_unknowns = NCARDS_PLAYER
        self.ndeck = NCARDS_DECK_BEGINNING
        self.decision_node = None

    def numcards(self):
        return len(self.cards)

    def put_card(self):
        if not self.cards:
            return None

        goodnesses = self._card_to_goodness()
        unbeatable = self._card_to_unbeatable_probability()

        card = max(self.cards, key=lambda c: goodnesses[c] + unbeatable[c])
        self.cards.remove(card)
        return card

    def put_card_more(self, strike):
        admissible_values = strike.card_values
        admissible_cards = frozenset(
            (suit, value)
            for (suit, value) in self.cards
            if value in admissible_values and suit != gcxt.trump
        )
        return self._choose_from(admissible_cards)

    def beat_this(self, card, strike):
        self._rival_puts_or_beats_with(card)
        suitable = frozenset(
            c for c in self.cards if beats(c, card)
        )
        return self._choose_from(suitable)

    def rival_beats(self, card, strike):
        self._rival_puts_or_beats_with(card)

    def rival_puts_unbeatable(self, card):
        assert card not in self.cards
        self._rival_puts_or_beats_with(card)

    def rival_takes(self, strike):
        assert mutually_exclusive(self.rivalcards, strike.all_cards,
                                  self.cards, self.blackset)
        self.rivalcards.update(strike.all_cards)

    def rival_takes_from_deck(self, n):
        assert n > 0
        self.nrival_unknowns += n
        self.ndeck -= n

    def take(self, strike):
        cards = strike.all_cards
        assert mutually_exclusive(cards, self.cards, self.rivalcards,
                                  self.blackset)
        self.cards.update(cards)

    def take_from_deck(self, cards):
        assert cards
        assert set(cards) <= self.blackset
        self.cards.update(cards)
        self.blackset.difference_update(cards)
        self.ndeck -= len(cards)

    def _rival_puts_or_beats_with(self, card):
        if card in self.rivalcards:
            self.rivalcards.remove(card)
        else:
            self.blackset.remove(card)
            self.nrival_unknowns -= 1

    def _card_to_goodness(self):
        values = {card_value(c) for c in self.cards}
        if len(values) == 1:
            return {
                c: 0 for c in self.cards
            }

        granularity = 1 / (len(values) - 1)
        card_value_to_goodness = {
            val: granularity * i
            for i, val in enumerate(sorted(values, reverse=True))
        }

        return {
            card: card_value_to_goodness[card_value(card)]
            for card in self.cards
        }

    def _unbeatable_probability(self, card):
        if any(beats(c, card) for c in self.rivalcards):
            return 0
        # P = (n + d - b)! * d! / (d - b)! / (n + d)!
        # b - number of black cards that can beat "card"
        # d is self.ndeck
        # n is self.nrival_unknowns
        b = sum(1 for c in self.blackset if beats(c, card))
        if self.ndeck < b:
            return 0
        else:
            n = self.nrival_unknowns
            d = self.ndeck
            P = factorial((n + d - b, d), (d - b, n + d))
            if self.ndeck <= 3:
                return P * 2
            else:
                return 0

    def _card_to_unbeatable_probability(self):
        return {
            card: self._unbeatable_probability(card)
            for card in self.cards
        }

    def _choose_from(self, cards):
        if not cards:
            return None

        card = min(cards, key=card_value)
        self.cards.remove(card)

        return card

    def _assert_invariants(self):
        assert mutually_exclusive(self.cards, self.rivalcards, self.blackset)
        assert self.nrival_unknowns + self.ndeck == len(self.blackset)
        assert self.ndeck >= 0


def mutually_exclusive(*sets):
    for i in range(len(sets)):
        for j in range(i+1, len(sets)):
            if sets[i] & sets[j]:
                return False
    return True


def make_autocheck_invariants(cls):
    def wrapper(self, meth, *args, **kwargs):
        self._assert_invariants()
        res = meth(self, *args, **kwargs)
        self._assert_invariants()
        return res

    for name, meth in cls.__dict__.items():
        if name.startswith('_'):
            continue

        newmeth = functools.partialmethod(wrapper, meth)
        functools.update_wrapper(newmeth, meth)
        setattr(cls, name, newmeth)


make_autocheck_invariants(SmartPlayer)
