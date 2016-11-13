"""
Implementation of a dumb player.

The dumb player's strategy is like this:
    * put the weakest card (alternatively: random card, which sucks);
    * beat with the weakest possible card (also, may choose random card);
    * put or not to put trump cards (varies).
"""

from itertools import chain

from common import card_value, beats, matching_by_value, RequestCode as rc, values_of


def scenario(send, cards, myturn):
    # Remember: we are not responsible to track EOG conditions here. This
    # is for the code that manages the game to handle.
    cards = set(cards)
    nrival_cards = len(cards)

    def choose_from(these):
        these = frozenset(these)
        if not these:
            return None

        card = min(these, key=card_value)
        cards.remove(card)
        return card

    def offense():
        """Return True if we made the rival give up"""
        nonlocal nrival_cards

        toff, tdef = set(), set()
        while nrival_cards > 0 and cards:
            if toff:
                offcard = choose_from(
                    matching_by_value(cards, values_of(chain(toff, tdef)))
                )
            else:
                offcard = choose_from(cards)
            send(offcard)
            if offcard is None:
                break

            toff.add(offcard)

            defcard = yield rc.DEFCARD
            if defcard is not None:
                tdef.add(defcard)
                nrival_cards -= 1
            else:
                unbeatables = choose_unbeatables(nrival_cards - 1,
                                                 values_of(chain(toff, tdef)))
                cards.difference_update(unbeatables)
                nrival_cards += len(unbeatables) + len(toff) + len(tdef)
                send(unbeatables)
                return True

        return False

    def choose_unbeatables(n, cardvalues):
        unbeatables = sorted(matching_by_value(cards, cardvalues, exclude_trumps=True),
                             key=card_value)
        del unbeatables[min(n, len(unbeatables)):]
        return frozenset(unbeatables)

    def defense():
        """Return True if we survived"""
        nonlocal nrival_cards

        toff, tdef = set(), set()
        while nrival_cards > 0 and cards:
            offcard = yield rc.OFFCARD
            if offcard is None:
                break

            nrival_cards -= 1
            toff.add(offcard)

            assert cards, "Logic error"
            suitable = frozenset(c for c in cards if beats(c, offcard))
            defcard = choose_from(suitable)
            send(defcard)
            if defcard is None:
                # i cannot beat the beatcard
                unbeatables = yield rc.UNBEATABLES
                assert len(unbeatables) < len(cards)
                toff |= unbeatables
                cards.update(toff, tdef)
                nrival_cards -= len(unbeatables)
                break

            tdef.add(defcard)

        return len(toff) == len(tdef)

    while cards and nrival_cards > 0:
        myturn = (yield from offense()) if myturn else (yield from defense())
        cards.update((yield rc.REPLENISHMENT))
        nrival_cards += yield rc.NUM_RIVAL_REPLENISHMENT

    yield rc.GAME_OVER
