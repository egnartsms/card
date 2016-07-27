import gcxt
from common import beats, random_deck, random_suit, GenHelper, NCARDS_PLAYER


def rungame(creator1, creator2):
    poff, pdef, deck = start_game(creator1, creator2)
    swapped = False
    noff = ndef = NCARDS_PLAYER

    def play_strike():
        """Return True if the defensive player survived, False otherwise"""
        nonlocal noff, ndef
        toff, tdef = 0, 0

        while ndef > 0:  # strike loop
            assert not poff.iswaiting and pdef.iswaiting

            offcard = poff.currval
            pdef.send(offcard)
            if offcard is None:
                break
            noff -= 1;  toff += 1

            defcard = pdef.currval  # Can be None or card
            poff.send(defcard)

            if defcard is None:
                # Defensive player takes all the cards.
                # Now: poff player waits for the max number of cards he
                # can put, pdef waits for the set of unbeatables he takes.
                assert poff.iswaiting and pdef.iswaiting
                unbeatables = poff.send(ndef - 1)
                pdef.send(unbeatables)
                ndef += toff + len(unbeatables)
                noff -= len(unbeatables)
                return False
            else:
                assert beats(defcard, offcard)
                ndef -= 1;  tdef += 1

        return True

    def replenish_cards():
        nonlocal noff, ndef
        assert poff.iswaiting and pdef.iswaiting

        n = min(len(deck), max(0, 6 - noff))
        # n2 = max(0, 6 - ndef)
        poff.send(deck[:n])
        del deck[:n]
        noff += n

        n = min(len(deck), max(0, 6 - ndef))
        pdef.send(deck[:n])
        del deck[:n]
        ndef += n

    while True:  # principal game loop
        survived = play_strike()
        replenish_cards()
        if noff == 0 or ndef == 0:
            if noff == 0 and ndef == 0:
                return None
            elif noff == 0:
                return not swapped
            else:
                return swapped

        if survived:
            poff, pdef = pdef, poff
            noff, ndef = ndef, noff
            swapped = not swapped


def start_game(creator1, creator2):
    deck = random_deck()
    gcxt.trump = random_suit()
    p1 = creator1(deck[:NCARDS_PLAYER], True)
    p2 = creator2(deck[NCARDS_PLAYER:NCARDS_PLAYER * 2], False)
    p1, p2 = GenHelper(p1), GenHelper(p2)
    del deck[:NCARDS_PLAYER * 2]
    return p1, p2, deck



