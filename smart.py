from itertools import takewhile

from common import card_value, beats, matching_by_value, RequestCode as rc,\
    NCARDS_PLAYER, deckset, values_of, mean_cardvalue


def scenario(send, cards, iattack, when_open_game=None):
    cards = set(cards)
    rival_num_unknowns = NCARDS_PLAYER
    blackset = set(deckset) - cards
    rival_knowns = set()

    def rival_num():
        return rival_num_unknowns + len(rival_knowns)

    def is_eog():
        return not cards or rival_num() == 0

    def draw_from(these):
        if not these:
            return None

        card = min(these, key=card_value)
        cards.remove(card)
        return card

    def offense():
        nonlocal rival_num_unknowns, rival_knowns, cards

        toff, tdef = set(), set()
        while not is_eog():
            if not toff:
                offcard = draw_from(cards)
            else:
                suitable = matching_by_value(cards, values_of(toff | tdef))
                if not blackset:
                    offcard = draw_from(suitable)
                elif not suitable:
                    offcard = None
                else:
                    weakest = min(suitable, key=card_value)
                    Mb = mean_cardvalue(blackset)
                    if card_value(weakest) <= Mb:
                        cards.remove(weakest)
                        offcard = weakest
                    else:
                        offcard = None

            send(offcard)
            if offcard is None:
                break
            toff.add(offcard)

            defcard = yield rc.DEFCARD
            if defcard is None:
                unbeatables = choose_unbeatables(rival_num() - 1, values_of(toff | tdef))
                assert not unbeatables & rival_knowns
                cards -= unbeatables
                toff |= unbeatables
                rival_knowns |= toff | tdef
                send(unbeatables)
                return True

            tdef.add(defcard)
            if defcard in rival_knowns:
                rival_knowns.remove(defcard)
            else:
                blackset.remove(defcard)
                rival_num_unknowns -= 1

        return False

    def choose_unbeatables(n, cardvalues):
        unbeatables = sorted(matching_by_value(cards, cardvalues), key=card_value)
        del unbeatables[min(n, len(unbeatables)):]

        if not blackset:
            return frozenset(unbeatables)
        else:
            Mb = mean_cardvalue(blackset)
            return frozenset(takewhile(lambda x: card_value(x) <= Mb, unbeatables))

    def defense():
        """Return True if we survived"""
        nonlocal rival_num_unknowns, rival_knowns, cards, blackset

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
            if not suitable:
                defcard = None
            else:
                defcard = min(suitable, key=card_value)
                if blackset:
                    # Here we can decide to give up
                    Mgiveup = mean_cardvalue(toff | tdef | cards)
                    n_old = len(cards) - 1
                    n_new = max(0, NCARDS_PLAYER - n_old)
                    Mb = mean_cardvalue(blackset)
                    Mbeat = (sum(card_value(c) for c in cards - {defcard}) + Mb * n_new)\
                        / (n_old + n_new)
                    if Mgiveup > Mbeat:
                        defcard = None

            send(defcard)
            if defcard is not None:
                cards.remove(defcard)
            else:
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

        return len(toff) == len(tdef)

    while not is_eog():
        iattack = (yield from offense()) if iattack else (yield from defense())
        my_replenishment = yield rc.REPLENISHMENT
        assert not my_replenishment & rival_knowns
        blackset -= my_replenishment
        cards |= my_replenishment
        rival_num_unknowns += yield rc.NUM_RIVAL_REPLENISHMENT
        if blackset and rival_num_unknowns == len(blackset):
            rival_num_unknowns = 0
            assert not rival_knowns & blackset
            rival_knowns |= blackset
            blackset.clear()
            # From this moment on, it is possible to give control to another algorithm
            if when_open_game:
                yield from when_open_game(send, cards, rival_knowns, iattack)
                break

    yield rc.GAME_OVER
