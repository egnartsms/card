from collections import Counter, namedtuple
from operator import attrgetter
from random import choice, shuffle

import gcxt


# A card: (suit, value).
# suit is one of 'clubs', 'diamonds', 'hearts', 'spades'.
# value is 6-10, 11 (knight), 12 (queen), 13 (king), 14 (ace).
Card = namedtuple('Card', ('suit', 'value'))


SUITS = ('clubs', 'diamonds', 'hearts', 'spades')

MIN_CARD_VALUE = 6
MAX_CARD_VALUE = 14

deckset = frozenset(
    Card(suit, v)
    for v in range(MIN_CARD_VALUE, MAX_CARD_VALUE + 1)
    for suit in SUITS
)
assert len(deckset) == 36

NUM_CARDS_PER_SUIT = len(deckset) // len(SUITS)


def beats(c1, c2, trump=None):
    if trump is None:
        trump = gcxt.trump
    assert trump is not None

    s1, v1 = c1
    s2, v2 = c2
    if s1 == s2:
        return v1 > v2
    else:
        return s1 == trump


def card_value(card, trump=None):
    """How many cards can beat this one"""
    if trump is None:
        trump = gcxt.trump
    assert trump is not None

    s, v = card
    if s != trump:
        return (v - MIN_CARD_VALUE) * (len(SUITS) - 1)
    else:
        return NUM_CARDS_PER_SUIT * (len(SUITS) - 1) + (v - MIN_CARD_VALUE)


class Strike:
    """Represents a move from one player to another"""
    def __init__(self, offensive=None, defensive=None):
        self.offensive = offensive or set()
        self.defensive = defensive or set()

    def add_offensive(self, card):
        self.offensive.add(card)

    def add_defensive(self, card):
        self.defensive.add(card)

    def add_offensives(self, cards):
        self.offensive.update(cards)

    def new_offensive_card(self, card):
        return Strike(self.offensive | {card}, self.defensive)

    def new_defensive_card(self, card):
        return Strike(self.offensive, self.defensive | {card})

    @property
    def beginning(self):
        return not self.offensive and not self.defensive

    @property
    def all_cards(self):
        return frozenset(self.offensive) | self.defensive

    @property
    def card_values(self):
        return frozenset(c.value for c in self.all_cards)

    def filter(self, cards):
        """Select those cards whose values are already on the table
        
        :return: iterable
        """
        cv = self.card_values
        return filter(lambda c: c.value in cv, cards)


def filter_cards_by_values(cards, table_cards):
    """Filter cards: take only those whose values are also in table_cards

    :param cards: iterable of cards
    :param table_cards: iterable of cards
    :return: iterable of cards
    """
    values = frozenset(map(attrgetter('value'), table_cards))
    return filter(lambda c: c.value in values, cards)


def random_suit():
    return choice(SUITS)


NCARDS_PLAYER = 6

NCARDS_DECK_BEGINNING = len(deckset) - 2 * NCARDS_PLAYER


def random_deck():
    """Return a deck in random order.

    :return: list of cards, full deck
    """
    deck = list(deckset)
    shuffle(deck)
    return deck


def factorial(nom, denom):
    res = Counter()
    for n in nom:
        res.update(Counter(range(n)))
    for n in denom:
        res.subtract(Counter(range(n)))

    p = 1.0
    for n, c in res.items():
        if c != 0:
            p *= pow(n, c)

    return p


novalue = object()


# Control codes
class CodesMetaclass(type):
    def __new__(mcs, name, bases, namespace):
        assert 'codes' in namespace
        codes = namespace['codes']
        for code in codes:
            assert isinstance(code, str)
            namespace[code] = code
        del namespace['codes']
        return super().__new__(mcs, name, bases, namespace)


class RequestCode(metaclass=CodesMetaclass):
    codes = (
        'DEFCARD',
        'OFFCARD',
        'NUM_UNBEATABLES',
        'UNBEATABLES',
        'REPLENISHMENT',
        'NUM_RIVAL_REPLENISHMENT',
        'GAME_OVER',
    )


# Wrapper for player algorithms
class Player:
    __slots__ = 'value', 'request_code', 'gen'

    def __init__(self, genfunc, mycards, myturn):
        def value_sender(val):
            self.value = val

        self.value = self.request_code = novalue
        self.gen = genfunc(value_sender, mycards, myturn)
        self.send(None)

    def send(self, value, request_code_must_be=None):
        if request_code_must_be is not None:
            assert self.request_code == request_code_must_be, "Logic error"

        # Previously generated value is reset.  The generator will assign a new value
        # in the course of its work.
        self.value = novalue
        self.request_code = self.gen.send(value)
