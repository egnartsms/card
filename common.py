from statistics import mean
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
    """How many cards can this one beat"""
    if trump is None:
        trump = gcxt.trump
    assert trump is not None

    s, v = card
    if s != trump:
        return (v - MIN_CARD_VALUE) * (len(SUITS) - 1)
    else:
        return NUM_CARDS_PER_SUIT * (len(SUITS) - 1) + (v - MIN_CARD_VALUE)


def values_of(cards):
    return frozenset(map(card_value, cards))


def matching_by_value(cards, cardvalues, exclude_trumps=False):
    """Filter cards: take only those whose values are in cardvalues

    :param cards: iterable of cards
    :param cardvalues: set of card values
    :param consider_trumps: if False, exclude trumps from result
    :return: frozenset of cards
    """
    def cond(c):
        return (not exclude_trumps or c.suit != gcxt.trump) and c.value in cardvalues

    return frozenset(filter(cond, cards))


def unbeatables(cards, cardvalues, maxn):
    """Return frozenset of suitable unbeatables"""
    suitable = sorted(matching_by_value(cards, cardvalues), key=card_value)
    del suitable[min(maxn, len(suitable)):]
    return frozenset(suitable)


def mean_cardvalue(cards):
    return mean(map(card_value, cards))


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

    def __init__(self, genfunc, mycards, iattack):
        def value_sender(val):
            self.value = val

        self.value = self.request_code = novalue
        self.gen = genfunc(value_sender, mycards, iattack)
        self.send(None)

    def send(self, value, request_code_must_be=None):
        if request_code_must_be is not None:
            assert self.request_code == request_code_must_be, "Logic error"

        # Previously generated value is reset.  The generator will assign a new value
        # in the course of its work.
        self.value = novalue
        self.request_code = self.gen.send(value)
