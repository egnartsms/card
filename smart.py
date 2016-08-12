from itertools import chain

from common import card_value, beats, filter_cards_by_values, RequestCode as rc,\
    NCARDS_PLAYER, deckset


def scenario(send, cards, myturn, consider_trumps):
    cards = set(cards)
    rival_num_unknowns = NCARDS_PLAYER
    blackset = set(deckset) - cards
    rival_knowns = set()
    junk = set()

    def rival_num():
        return rival_num_unknowns + len(rival_knowns)

    def is_eog():
        return not cards or rival_num() == 0

    def draw_from(these):
        these = frozenset(these)
        if not these:
            return None

        card = min(these, key=card_value)
        cards.remove(card)
        return card

    def offense():
        nonlocal rival_num_unknowns, rival_knowns, cards, junk
        toff, tdef = set(), set()
        while not is_eog():
            if toff:
                offcard = draw_from(
                    filter_cards_by_values(cards, chain(toff, tdef), consider_trumps)
                )
            else:
                offcard = draw_from(cards)
            send(offcard)
            if offcard is None:
                break

            toff.add(offcard)

            defcard = yield rc.DEFCARD
            if defcard is not None:
                tdef.add(defcard)
                if defcard in rival_knowns:
                    rival_knowns.remove(defcard)
                else:
                    blackset.remove(defcard)
                    rival_num_unknowns -= 1
            else:
                unbeatables = choose_unbeatables(rival_num() - 1, chain(toff, tdef))
                assert not unbeatables & rival_knowns
                cards -= unbeatables
                toff |= unbeatables
                rival_knowns |= toff | tdef
                send(unbeatables)
                return True

        junk |= toff | tdef

        return False

    def choose_unbeatables(n, table_cards):
        unbeatables = sorted(filter_cards_by_values(cards, table_cards, consider_trumps),
                             key=card_value)
        del unbeatables[min(n, len(unbeatables)):]
        return frozenset(unbeatables)

    def defense():
        """Return True if we survived"""
        nonlocal rival_num_unknowns, rival_knowns, cards, blackset, junk

        toff, tdef = set(), set()
        while not is_eog():
            offcard = yield rc.OFFCARD
            if offcard is None:
                break

            toff.add(offcard)

            if offcard in rival_knowns:
                rival_knowns.remove(offcard)
            else:
                blackset.remove(offcard)
                rival_num_unknowns -= 1

            assert cards, "Logic error"
            suitable = frozenset(c for c in cards if beats(c, offcard))
            defcard = draw_from(suitable)
            send(defcard)
            if defcard is None:
                # i cannot beat the beatcard
                unbeatables = yield rc.UNBEATABLES
                assert len(unbeatables) < len(cards)
                toff |= unbeatables
                cards |= (toff | tdef)
                rival_knowns -= unbeatables
                rival_num_unknowns -= len(blackset & unbeatables)
                blackset -= unbeatables
                break

            tdef.add(defcard)

        if len(toff) == len(tdef):
            junk |= toff | tdef

        return len(toff) == len(tdef)

    while not is_eog():
        myturn = (yield from offense()) if myturn else (yield from defense())
        my_replenishment = yield rc.REPLENISHMENT
        assert not my_replenishment & rival_knowns
        blackset -= my_replenishment
        cards |= my_replenishment
        rival_num_unknowns += yield rc.NUM_RIVAL_REPLENISHMENT

    yield rc.GAME_OVER
