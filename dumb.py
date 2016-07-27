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
    NCARDS_PLAYER


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

            c_off.add(offcard)
            yield offcard

            defcard = yield
            if defcard is not None:
                c_def.add(defcard)
            else:
                nput = yield
                yield from put_unbeatables(nput, chain(c_off, c_def))
                return True

        return False

    def put_unbeatables(n, table_cards):
        unbeatables = sorted(filter_cards_by_values(cards, table_cards),
                             key=card_value)
        del unbeatables[min(n, len(unbeatables)):]
        cards.difference_update(unbeatables)
        yield unbeatables

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
                assert len(unbeatables) < len(cards)
                c_off |= unbeatables
                cards.update(unbeatables)
                return False
        return True

    while True:
        assert cards, "Logic error"
        myturn = (yield from offense()) if myturn else (yield from defense())
        if len(cards) < NCARDS_PLAYER:
            cards.update((yield))
