import gcxt
from common import beats, random_deck, random_suit, GenHelper, NCARDS_PLAYER,\
    PUT_CARD, READY_TO_BEAT, BEAT_WITH, TAKE_UNBEATABLES, GET_MORE_CARDS


def rungame(creator1, creator2):
    def play_strike():
        """Return True if the defensive player survived, False otherwise"""
        nonlocal noff, ndef

        assert pdef.currval == (READY_TO_BEAT, None)

        while ndef > 0:  # strike loop
            poff.send()
            code, offcard = poff.currval
            assert code == PUT_CARD



            if strike.beginning:
                offc = poffense.put_card()
            else:
                offc = poffense.put_card_more(strike)

            if offc is None:
                pdefense.rival_ends_strike(strike)
                return True

            strike.add_offensive(offc)

            defc = pdefense.beat_this(offc, strike)
            if defc is None:
                # Defensive player takes all the cards
                finish_strike_put_cards(poffense, pdefense, strike)
                poffense.rival_takes(strike)
                pdefense.take(strike)
                return False

            assert beats(defc, offc)
            strike.add_defensive(defc)
            poffense.rival_beats(defc, strike)

        return True

    poff, pdef, deck = start_game(creator1, creator2)
    swapped = False
    noff = ndef = NCARDS_PLAYER



    while True:  # principal game loop
        survived = play_strike(poffense, pdefense)
        replenish_cards(poffense, pdefense, deck)
        if poffense.numcards() == 0 or pdefense.numcards() == 0:
            if poffense.numcards() == 0 and pdefense.numcards() == 0:
                return None
            elif poffense.numcards() == 0:
                return not swapped
            else:
                return swapped
        if survived:
            poffense, pdefense = pdefense, poffense
            swapped = not swapped




def play(creator1, creator2):
    """Return True if first won, None for draw"""
    poffense, pdefense, deck = start_game(creator1, creator2)
    swapped = False
    while True:  # principal game loop
        survived = play_strike(poffense, pdefense)
        replenish_cards(poffense, pdefense, deck)
        if poffense.numcards() == 0 or pdefense.numcards() == 0:
            if poffense.numcards() == 0 and pdefense.numcards() == 0:
                return None
            elif poffense.numcards() == 0:
                return not swapped
            else:
                return swapped
        if survived:
            poffense, pdefense = pdefense, poffense
            swapped = not swapped


def finish_strike_put_cards(poffense, pdefense, strike):
    """poffense puts everything he can and wants to put"""
    assert len(strike.offensive) == len(strike.defensive) + 1
    assert pdefense.numcards() >= 1
    can_put = pdefense.numcards() - 1
    poffense.rival_beats(None, strike)
    cards = poffense.put_unbeatables(strike, can_put)
    assert isinstance(cards, frozenset)
    assert len(cards) <= can_put
    strike.add_offensives(cards)
    pdefense.rival_puts_unbeatables(cards, strike)


def replenish_cards(p1, p2, deck):
    n1 = max(0, 6 - p1.numcards())
    n2 = max(0, 6 - p2.numcards())
    n1 = min(len(deck), n1)
    if n1 > 0:
        p1.take_from_deck(frozenset(deck[:n1]))
        p2.rival_takes_from_deck(n1)
        del deck[:n1]
    n2 = min(len(deck), n2)
    if n2 > 0:
        p2.take_from_deck(frozenset(deck[:n2]))
        p1.rival_takes_from_deck(n2)
        del deck[:n2]


def start_game(creator1, creator2):
    deck = random_deck()
    gcxt.trump = random_suit()
    p1 = creator1(deck[:NCARDS_PLAYER], True)
    p2 = creator2(deck[NCARDS_PLAYER:NCARDS_PLAYER * 2], False)
    p1, p2 = GenHelper(p1), GenHelper(p2)
    del deck[:NCARDS_PLAYER * 2]
    return p1, p2, deck



