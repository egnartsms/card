from itertools import chain
from random import choice

from util import to_frozenset
from common import card_value, beats, filter_cards_by_values, RequestCode as rc,\
    NCARDS_DECK_BEGINNING, NCARDS_PLAYER, deckset


def scenario(send, cards, myturn):
    rival_num_unknowns = NCARDS_PLAYER
    blackset = set(deckset) - cards
    rival_knowns = set()
    cards = set(cards)

    def offense():
        pass

    def choose_unbeatables(n, table_cards):
        pass

    def defense():
        pass

    while cards and (rival_num_unknowns > 0 or rival_knowns) > 0:
        myturn = (yield from offense()) if myturn else (yield from defense())
        cards.update((yield rc.REPLENISHMENT))
        nrival_cards += yield rc.NUM_RIVAL_REPLENISHMENT

    yield rc.GAME_OVER


    pass
