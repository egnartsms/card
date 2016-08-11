import gcxt
from common import beats, random_deck, random_suit, NCARDS_PLAYER, RequestCode as rc,\
    Player


def rungame(scenario1, scenario2):
    poff, coff, pdef, cdef, deck = start_game(scenario1, scenario2)
    coff = set(coff)
    cdef = set(cdef)
    swapped = False

    def play_strike():
        """Return True if the defensive player survived, False otherwise"""
        assert cdef
        toff, tdef = set(), set()

        while coff and cdef:  # strike loop
            offcard = poff.value
            pdef.send(offcard, rc.OFFCARD)
            if offcard is None:
                assert toff
                break
            coff.remove(offcard)
            toff.add(offcard)

            defcard = pdef.value  # Can be None or card
            poff.send(defcard, rc.DEFCARD)

            if defcard is None:
                # Defensive player takes all the cards.
                # Now: pdef waits for the set of unbeatables he takes.
                unbeatables = poff.value
                pdef.send(unbeatables, rc.UNBEATABLES)
                cdef.update(toff, tdef, unbeatables)
                coff.difference_update(unbeatables)
                return False
            else:
                assert beats(defcard, offcard)
                cdef.remove(defcard)
                tdef.add(defcard)

        return True

    def replenish_cards():
        noff = min(len(deck), max(0, NCARDS_PLAYER - len(coff)))
        roff = frozenset(deck[:noff])
        del deck[:noff]

        ndef = min(len(deck), max(0, NCARDS_PLAYER - len(cdef)))
        rdef = frozenset(deck[:ndef])
        del deck[:ndef]

        poff.send(roff, rc.REPLENISHMENT)
        pdef.send(rdef, rc.REPLENISHMENT)
        poff.send(len(rdef), rc.NUM_RIVAL_REPLENISHMENT)
        pdef.send(len(roff), rc.NUM_RIVAL_REPLENISHMENT)

        coff.update(roff)
        cdef.update(rdef)

    while True:  # principal game loop
        survived = play_strike()
        replenish_cards()
        if not coff or not cdef:
            assert poff.request_code == rc.GAME_OVER
            assert pdef.request_code == rc.GAME_OVER
            if not coff and not cdef:
                return None
            elif not coff:
                return not swapped
            else:
                return swapped

        if survived:
            poff, pdef = pdef, poff
            coff, cdef = cdef, coff
            swapped = not swapped


def start_game(scenario1, scenario2):
    """Return (p1, cards1, p2, cards2, deck)"""
    deck = random_deck()
    gcxt.trump = random_suit()
    cards1 = deck[:NCARDS_PLAYER]
    p1 = Player(scenario1, frozenset(cards1), True)
    cards2 = deck[NCARDS_PLAYER:NCARDS_PLAYER * 2]
    p2 = Player(scenario2, frozenset(cards2), False)
    del deck[:NCARDS_PLAYER * 2]
    return p1, cards1, p2, cards2, deck
