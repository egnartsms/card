"""
Implementation of a dumb player.

The dumb player's strategy is like this:
    * put the weakest card (alternatively: random card, which sucks);
    * beat with the weakest possible card (also, may choose random card);
    * put or not to put trump cards (varies).
"""

from itertools import chain
from random import choice

import gcxt
from common import card_value, beats, filter_cards_by_values, \
    NCARDS_PLAYER


class DumbPlayer:
    """Player algorithm with simple strategy.
    
    Possible options are:
        * 'put-more-trumps'
        * 'choose-card': 'random', 'min'
    """
    def __init__(self, options, cards):
        self.options = options
        self.cards = set(cards)

    def numcards(self):
        return len(self.cards)

    def put_card(self):
        return self._choose_from(self.cards)

    def put_card_more(self, strike):
        admissible_cards = self._admissible_cards(strike)
        return self._choose_from(admissible_cards)

    def put_unbeatables(self, strike, nmax):
        cards = frozenset(
            sorted(self._admissible_cards(strike), key=card_value)[:nmax]
        )
        self.cards -= cards
        return cards

    def beat_this(self, card, strike):
        suitable = frozenset(
            c for c in self.cards if beats(c, card)
        )
        return self._choose_from(suitable)

    def rival_beats(self, card, strike):
        pass

    def rival_puts_unbeatables(self, cards, strike):
        pass

    def rival_ends_strike(self, strike):
        pass

    def rival_takes(self, strike):
        pass

    def rival_takes_from_deck(self, n):
        pass

    def take(self, strike):
        self.cards.update(strike.all_cards)

    def take_from_deck(self, cards):
        self.cards.update(cards)

    def _admissible_cards(self, strike):
        res = strike.filter(self.cards)
        if not self.options.get('put-more-trumps', True):
            res = filter(lambda c: c[1] != gcxt.trump, res)
        return frozenset(res)

    def _choose_from(self, cards):
        if not cards:
            return None

        if self.options['choose-card'] == 'min':
            card = min(cards, key=card_value)
        elif self.options['choose-card'] == 'random':
            card = choice(list(cards))
        else:
            raise RuntimeError("Invalid value for 'choose-card' option")

        self.cards.remove(card)

        return card


def play(cards, myturn, options):
    # Remember: we are not responsible to track EOG conditions here.  This is
    # for the code that manages the game to handle.
    cards = set(cards)

    def choose_from(these):
        if not these:
            return None

        if options['choose-card'] == 'min':
            card = min(these, key=card_value)
        elif options['choose-card'] == 'random':
            card = choice(list(these))
        else:
            raise RuntimeError("Invalid value for 'choose-card' option")

        cards.remove(card)
        return card

    def offense():
        """Return True if the rival failed to beat our cards"""
        c_off, c_def = set(), set()
        while cards:
            if c_off:
                offcard = choose_from(
                    filter_cards_by_values(cards, chain(c_off, c_def))
                )
            else:
                offcard = choose_from(cards)
            if offcard is None:
                break

            yield offcard
            defcard = yield
            if defcard is not None:
                c_def.add(defcard)
            else:
                return True

        return False

    def defense():
        """Return True if we survived"""
        c_off = set()
        while True:
            offcard = yield
            if offcard is None:
                break

            assert cards, "Logic error"

            c_off.add(offcard)
            suitable = frozenset(c for c in cards if beats(c, offcard))
            defcard = choose_from(suitable)
            if defcard is not None:
                yield defcard
            else:
                # i cannot beat the beatcard
                unbeatables = yield
                c_off |= unbeatables
                cards.update(unbeatables)
                return False
        return True

    while True:
        assert cards, "Logic error"
        myturn = (yield from offense()) if myturn else (yield from defense())
        if len(cards) < NCARDS_PLAYER:
            cards.update((yield))
