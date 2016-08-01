"""
Implementation of a dumb player.

The dumb player's strategy is like this:
    * put the weakest card (alternatively: random card, which sucks);
    * beat with the weakest possible card (also, may choose random card);
    * put or not to put trump cards (varies).
"""

from itertools import chain
from random import choice


from common import card_value, beats, filter_cards_by_values, \
    NCARDS_PLAYER, novalue


class Player:
    __slots__ = 'value', 'gen'

    def __init__(self, *args, **kwargs):
        self.value = None
        self.gen = self._scenario(*args, **kwargs)
        self.send(None)

    def send(self, value):
        self.value = novalue
        self.gen.send(value)

    def _scenario(self, cards, myturn, options):
        # Remember: we are not responsible to track EOG conditions here. This
        # is for the code that manages the game to handle.
        cards = set(cards)

        def choose_from(these):
            if not isinstance(these, (set, frozenset)):
                these = frozenset(these)

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
            toff, tdef = set(), set()
            while True:
                if toff:
                    offcard = choose_from(
                        filter_cards_by_values(cards, chain(toff, tdef))
                    )
                else:
                    offcard = choose_from(cards)
                self.value = offcard
                if offcard is None:
                    break

                toff.add(offcard)

                defcard = yield
                if defcard is not None:
                    tdef.add(defcard)
                else:
                    nput = yield
                    put_unbeatables(nput, chain(toff, tdef))
                    return True

            return False

        def put_unbeatables(n, table_cards):
            unbeatables = sorted(filter_cards_by_values(cards, table_cards),
                                 key=card_value)
            del unbeatables[min(n, len(unbeatables)):]
            cards.difference_update(unbeatables)
            self.value = frozenset(unbeatables)

        def defense():
            """Return True if we survived"""
            toff, tdef = set(), set()
            while True:
                offcard = yield
                if offcard is None:
                    break

                assert cards, "Logic error"
                toff.add(offcard)

                suitable = frozenset(c for c in cards if beats(c, offcard))
                defcard = choose_from(suitable)
                self.value = defcard
                if defcard is None:
                    # i cannot beat the beatcard
                    unbeatables = yield
                    assert len(unbeatables) < len(cards)
                    toff |= unbeatables
                    cards.update(toff, tdef)
                    break

                tdef.add(defcard)

            return len(toff) == len(tdef)

        while True:
            assert cards, "Logic error"
            myturn = (yield from offense()) if myturn else (yield from defense())
            if len(cards) < NCARDS_PLAYER:
                cards.update((yield))
