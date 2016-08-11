import operator
from itertools import combinations, chain, groupby

from common import beats, filter_cards_by_values, card_value
from util import recordtype


MAXDEPTH = 3


Node = recordtype('Node', (
    'offense_cards',
    'defense_cards',
    'myturn',
    'internode',
    'internode_count',
    'subnodes'
))


Internode = recordtype('Internode', (
    'moves',
    'myturn',
    ('estimate', None),
    ('bestmove', None),
))


def node_estimate(obj):
    if isinstance(obj, float):
        return obj
    if isinstance(obj, Node):
        return node_estimate(obj.internode)
    if isinstance(obj, Internode):
        return obj.estimate
    assert 0, "Invalid node object to estimate"


def make_internode(moves, myturn):
    """Make a new internode and compute its estimate and best move"""
    subestimates = tuple((move, node_estimate(subnode))
                         for move, subnode in moves.items())
    bestmove, est = (max if myturn else min)(subestimates, key=operator.itemgetter(1))

    return Internode(
        moves=moves,
        myturn=myturn,
        estimate=est,
        bestmove=bestmove
    )


def build_decision_tree(offense_cards, defense_cards, myturn, levels):
    def check_eog(c_off, c_def):
        if c_off and c_def:
            return None
        elif not c_off and not c_def:
            # A draw
            return 0.5
        elif not c_off:
            return 1.0 if myturn else 0.0
        else:
            assert not c_def
            return 0.0 if myturn else 1.0

    # Terminology:
    #   c_off, c_def - cards of offensive and defensive players that
    # they have on the hands;
    #   t_off, t_def - cards on the table (already put).
    # Next strike nodes: {(t_off, t_def): Node}
    subnodes = {}
    # Nodes within this strike: {(t_off, t_def): Internode}
    internodes = {}

    def offensive(c_off, c_def, t_off, t_def):
        if (t_off, t_def) in internodes:
            return internodes[t_off, t_def]

        res = check_eog(c_off, c_def)
        if res is not None:
            internodes[t_off, t_def] = res
            return res

        if t_off:
            cards = filter_cards_by_values(c_off, chain(t_off, t_def))
        else:
            cards = c_off
        moves = {
            c: defensive(c_off - {c}, c_def, t_off | {c}, t_def, c)
            for c in cards
        }
        if t_off:
            moves[None] = lookup_subnode(t_off, t_def)
        node = make_internode(moves, myturn)
        internodes[t_off, t_def] = node
        return node

    def defensive(c_off, c_def, t_off, t_def, beatcard):
        assert beatcard in t_off
        assert beatcard not in c_off

        if (t_off, t_def) in internodes:
            return internodes[t_off, t_def]

        variants = frozenset(c for c in c_def if beats(c, beatcard))
        moves = {
            c: offensive(c_off, c_def - {c}, t_off, t_def | {c})
            for c in variants
        }
        moves[None] = put_unbeatables(c_off, c_def, t_off, t_def)
        node = make_internode(moves, not myturn)
        internodes[t_off, t_def] = node
        return node

    def put_unbeatables(c_off, c_def, t_off, t_def):
        assert len(t_off) == len(t_def) + 1
        assert len(c_def) >= 1

        if (t_off, t_def) in internodes:
            return internodes[t_off, t_def]

        more_cards = frozenset(filter_cards_by_values(c_off,
                                                      chain(t_off, t_def)))
        n = min(len(c_def) - 1, len(more_cards))
        moves = {
            frozenset(cards): lookup_subnode(t_off.union(cards), t_def)
            for cards in combinations(more_cards, n)
        }
        node = make_internode(moves, myturn)
        internodes[t_off, t_def] = node
        return node

    def lookup_subnode(t_off, t_def):
        assert len(t_off) >= len(t_def)
        if (t_off, t_def) not in subnodes:
            subnodes[t_off, t_def] = (
                build_decision_tree(
                    offense_cards - t_off,
                    defense_cards | t_off,
                    myturn,
                    levels - 1
                ) if len(t_off) > len(t_def) else
                build_decision_tree(
                    defense_cards - t_def,
                    offense_cards - t_off,
                    not myturn,
                    levels - 1
                )
            )
        return subnodes[t_off, t_def]

    res = check_eog(offense_cards, defense_cards)
    if res is not None:
        return res

    if levels == 0:
        # Estimate my cards vs rival's cards
        p1, p2 = cardset_relation(offense_cards, defense_cards)
        return p1 if myturn else p2

    principal_internode = offensive(offense_cards, defense_cards,
                                    frozenset(), frozenset())

    return Node(
        offense_cards=offense_cards,
        defense_cards=defense_cards,
        myturn=myturn,
        internode=principal_internode,
        internode_count=len(internodes),
        subnodes=tuple(subnodes.values()),
    )


def build_tree(mycards, hiscards, iput):
    """Build decision tree which starts with offensive.
    :param mycards: iterable of cards
    :param hiscards: iterable of cards
    :param boolean iput:
    """
    if iput:
        offense_cards = frozenset(mycards)
        defense_cards = frozenset(hiscards)
    else:
        offense_cards = frozenset(hiscards)
        defense_cards = frozenset(mycards)

    return build_decision_tree(offense_cards, defense_cards, iput, MAXDEPTH)


def cardset_relation(cards1, cards2):
    """How card sets relate one to another.

    :param cards1: iterables of cards
    :param cards2: iterables of cards
    :return (float, float): sum of these numbers is 1.0.
    """
    cards = sorted(
        chain(
            ((card_value(c), 1) for c in cards1),
            ((card_value(c), 2) for c in cards2)
        ),
        key=operator.itemgetter(0),
        reverse=True
    )
    met1, met2 = 0, 0
    p1, p2 = 0, 0
    for key, cardgroup in groupby(cards, operator.itemgetter(0)):
        values = tuple(map(operator.itemgetter(1), cardgroup))
        justmet1 = sum(1 for v in values if v == 1)
        justmet2 = sum(1 for v in values if v == 2)
        p1 += met1 * justmet2
        p2 += met2 * justmet1
        met1 += justmet1
        met2 += justmet2

    if p1 + p2 == 0:
        return 0.5, 0.5
    else:
        return p1 / (p1 + p2), p2 / (p1 + p2)


def vis_tree_structure(tree):
    if not isinstance(tree, Node):
        return tree

    return {c: vis_tree_structure(sub) for c, sub in tree.moves.items()}


# def deepen1(node):
#     """Enlarge the tree by 1 more level downwards and update estimates.
#
#     :param node: Node
#     """
#     if not isinstance(node, Node):
#         return
#
#     for subnode in node.moves.values():
#         deepen1(subnode)
#
#     # Select those moves that lead to jump to the next level where we still have
#     # Nones instead of nodes.  These are leaves that we want to grow our tree
#     # at.  In a defense node there can be no such leaves (cause a strike cannot
#     # finish after beating or giving up -- the offensive player should be able
#     # to put more cards after that).
#     if node.beatcard:
#         _recompute_estimate_for(node)
#         return
#
#     xmoves = frozenset(
#         move for move, subnode in node.moves.items() if subnode is None
#     )
#     # The following is due to the game scheme
#     assert all(m is None or isinstance(m, frozenset) for m in xmoves)
#
#     for cards in xmoves:
#         node.moves[cards] = (
#             build_offense_subtree(
#                 node.offense_cards - cards,
#                 node.defense_cards | cards | node.strike.all_cards,
#                 node.myturn,
#                 Strike(),
#                 0, 1
#             )
#             if isinstance(cards, frozenset) else
#             build_offense_subtree(
#                 node.defense_cards,
#                 node.offense_cards,
#                 not node.myturn,
#                 Strike(),
#                 0, 1
#             )
#         )
#         estimate(node.moves[cards])
#
#     _recompute_estimate_for(node)


def tree_height(node):
    raise NotImplementedError


def tree_count(node):
    if isinstance(node, Node):
        return 1 + node.internode_count + sum(tree_count(x) for x in node.subnodes)
    else:
        return 1
