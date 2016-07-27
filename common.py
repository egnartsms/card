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


WAITCARD = 'waitcard'

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


class ControlCode(metaclass=CodesMetaclass):
    codes = (
        'PUT_OFFCARD',
        'GET_DEFCARD',
        'PUT_DEFCARD'
        'GET_OFFCARD',
        'TAKE_UNBEATABLES',
        'GET_MORE_CARDS',
    )


class GenHelper:
    __slots__ = 'gen', 'currval'

    def __init__(self, gen):
        self.gen = gen
        self.currval = self.gen.send(None)

    def send(self, obj):
        self.currval = self.gen.send(obj)
        return self.currval

    @property
    def iswaiting(self):
        return self.currval is None
