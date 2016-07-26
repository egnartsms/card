"""
Implementation of a smart player.

Smart player remembers all the cards and tries to determine which cards has
the opponent. This information is used for decision making.
"""
import functools
from itertools import islice

import gcxt
from common import deckset, card_value, NCARDS_DECK_BEGINNING, NCARDS_PLAYER,\
    beats, Strike
from decision_tree import build_defense_subtree, build_offense_subtree, Node,\
    deepen1, MAXDEPTH, node_estimate, tree_height, tree_count


class SmartPlayer:
    def __init__(self, cards):
        assert len(cards) == NCARDS_PLAYER
        self.cards = set(cards)
        self.blackset = set(deckset - self.cards)
        self.rivalcards = set()
        self.nrival_unknowns = NCARDS_PLAYER
        self.ndeck = NCARDS_DECK_BEGINNING
        # None: deck is not empty; True: build a tree on next decision
        self.decision_node = None

    def numcards(self):
        return len(self.cards)

    def put_card(self):
        print("Smart puts")
        self._check_endgame_iput()
        if self.decision_node:
            self._assert_decision_node_correctness(myturn=True, iput=True)
            card = self.decision_node.bestmove
            assert card is not None
            self.cards.remove(card)
            self.decision_node = self.decision_node.moves[card]
            return card
        else:
            return self._choose_from(self.cards)

    def put_card_more(self, strike):
        if isinstance(self.decision_node, int):
            return None
        if self.decision_node:
            assert isinstance(self.decision_node, Node)
            self._assert_decision_node_correctness(myturn=True, iput=True)
            move = self.decision_node.bestmove
            self.decision_node = self.decision_node.moves[move]
            if move is not None:  # move can be None or card
                self.cards.remove(move)
            return move
        else:
            admissible_cards = frozenset(filter(lambda c: c.suit != gcxt.trump,
                                                strike.filter(self.cards)))
            return self._choose_from(admissible_cards)

    def put_unbeatables(self, strike, nlimit):
        if self.decision_node:
            assert isinstance(self.decision_node, Node)
            self._assert_decision_node_correctness(myturn=True, iput=True)
            unbeatables = self.decision_node.bestmove
            self.cards -= unbeatables
            self.decision_node = self.decision_node.moves[unbeatables]
            return unbeatables
        else:
            res = frozenset(islice(
                filter(lambda c: c.suit != gcxt.trump,
                       strike.filter(self.cards)),
                0, nlimit
            ))
            self.cards -= res
            return res

    def beat_this(self, beatcard, strike):
        assert beatcard in strike.offensive
        self._rival_puts_or_beats_with(beatcard)
        self._check_endgame_ibeat(beatcard, strike.offensive == {beatcard})
        if self.decision_node:
            self._assert_decision_node_correctness(myturn=True, iput=False)
            move = self.decision_node.bestmove
            self.decision_node = self.decision_node.moves[move]
            if move is not None:  # move can be None or card
                self.cards.remove(move)
            return move
        else:
            suitable = frozenset(
                c for c in self.cards if beats(c, beatcard)
            )
            return self._choose_from(suitable)

    def rival_beats(self, card, strike):
        # Remember that card can be None, meaning that the rival could not beat
        # the card i just put him
        if self.decision_node:
            self._assert_decision_node_correctness(myturn=False, iput=True)
            self.decision_node = self.decision_node.moves[card]
        if card:
            self._rival_puts_or_beats_with(card)

    def rival_puts_unbeatables(self, cards, strike):
        assert isinstance(cards, frozenset)
        assert mutually_exclusive(cards, self.cards)

        if self.decision_node:
            self._assert_decision_node_correctness(myturn=False, iput=False)
            self.decision_node = self.decision_node.moves[cards]

        knowns = self.rivalcards & cards
        unknowns = cards - knowns
        assert unknowns <= self.blackset
        self.rivalcards -= knowns
        self.blackset -= unknowns
        self.nrival_unknowns -= len(unknowns)

    def rival_ends_strike(self, strike):
        if self.decision_node:
            self._assert_decision_node_correctness(myturn=False, iput=False)
            self.decision_node = self.decision_node.moves[None]

    def rival_takes(self, strike):
        assert mutually_exclusive(self.rivalcards, strike.all_cards,
                                  self.cards, self.blackset)
        # if self.decision_node:
        #     self._assert_decision_node_correctness(myturn=False, iput=True)
        #     self.decision_node = self.decision_node.moves[None]

        self.rivalcards.update(strike.all_cards)

    def rival_takes_from_deck(self, n):
        assert n > 0
        assert self.decision_node is None
        self.nrival_unknowns += n
        self.ndeck -= n
        self._check_deck_exhausted()

    def take(self, strike):
        cards = strike.all_cards
        assert mutually_exclusive(cards, self.cards, self.rivalcards,
                                  self.blackset)
        self.cards.update(cards)

    def take_from_deck(self, cards):
        assert cards
        assert cards <= self.blackset
        self.cards |= cards
        self.blackset -= cards
        self.ndeck -= len(cards)
        self._check_deck_exhausted()

    def _rival_puts_or_beats_with(self, card):
        if card in self.rivalcards:
            self.rivalcards.remove(card)
        else:
            self.blackset.remove(card)
            self.nrival_unknowns -= 1

    def _check_deck_exhausted(self):
        if self.ndeck == 0:
            self.rivalcards |= self.blackset
            self.blackset = set()
            self.nrival_unknowns = 0
            self.decision_node = True

    def _check_endgame_iput(self):
        """If 'decision_node' attr is True, assign it a new tree.

        :param beatcard: the card we should beat now, or None if we offense.
        """
        if self.decision_node is None:
            return

        if self.decision_node is True:
            assert self.ndeck == 0
            assert not self.blackset
            assert self.nrival_unknowns == 0
            self.decision_node = build_offense_subtree(
                self.cards,
                self.rivalcards,
                True,
                Strike(),
                0, MAXDEPTH
            )
            estimate(self.decision_node)
            print("Create decision tree, i put.",
                  "Height", tree_height(self.decision_node),
                  "Count", tree_count(self.decision_node))
        else:
            print("Deepening decision tree, i put.",
                  "Height", tree_height(self.decision_node),
                  "Count", tree_count(self.decision_node))
            deepen1(self.decision_node)
            print("Deepening done.",
                  "Height", tree_height(self.decision_node),
                  "Count", tree_count(self.decision_node))

    def _check_endgame_ibeat(self, beatcard, do_deepen):
        if self.decision_node is None:
            return

        if self.decision_node is True:
            self.decision_node = build_defense_subtree(
                self.rivalcards,
                self.cards,
                True,
                beatcard,
                Strike(offensive={beatcard}),
                0, MAXDEPTH
            )
            estimate(self.decision_node)
            print("Create decision tree, i beat.",
                  "Height", tree_height(self.decision_node),
                  "Count", tree_count(self.decision_node))
        else:
            # decision_node corresponds to the position our rival just was,
            # before he decided to put "beatcard"
            self.decision_node = self.decision_node.moves[beatcard]
            if do_deepen:
                print("Deepening decision tree, i beat.",
                      "Height", tree_height(self.decision_node),
                      "Count", tree_count(self.decision_node))
                deepen1(self.decision_node)
                print("Deepening done.",
                      "Height", tree_height(self.decision_node),
                      "Count", tree_count(self.decision_node))

    def _choose_from(self, cards):
        if not cards:
            return None

        card = min(cards, key=card_value)
        self.cards.remove(card)

        return card

    def _assert_decision_node_correctness(self, myturn, iput):
        assert not self.blackset
        assert self.nrival_unknowns == 0
        assert self.decision_node.myturn == myturn
        if iput:
            assert self.decision_node.offense_cards == self.cards
            assert self.decision_node.defense_cards == self.rivalcards
        else:
            assert self.decision_node.offense_cards == self.rivalcards
            assert self.decision_node.defense_cards == self.cards

    def _assert_invariants(self):
        assert mutually_exclusive(self.cards, self.rivalcards, self.blackset)
        assert self.nrival_unknowns + self.ndeck == len(self.blackset)
        assert self.ndeck >= 0


def mutually_exclusive(*sets):
    for i in range(len(sets)):
        for j in range(i+1, len(sets)):
            if sets[i] & sets[j]:
                return False
    return True


def make_autocheck_invariants(cls):
    def wrapper(self, meth, *args, **kwargs):
        self._assert_invariants()
        res = meth(self, *args, **kwargs)
        self._assert_invariants()
        return res

    for name, meth in cls.__dict__.items():
        if name.startswith('_'):
            continue

        newmeth = functools.partialmethod(wrapper, meth)
        functools.update_wrapper(newmeth, meth)
        setattr(cls, name, newmeth)


make_autocheck_invariants(SmartPlayer)
