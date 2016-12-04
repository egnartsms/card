import operator
from itertools import combinations, chain, groupby

from recordclass import recordclass

from common import beats, matching_by_value, values_of, card_value


Node = recordclass('Node', (
    'offense_cards',
    'defense_cards',
    'iattack',
    # HACK: for leaf nodes, we store estimate here, not internode.  When deepen,
    # this field is assigned a real internode.
    'internode',
))

Internode = recordclass('Internode', (
    'moves',
    'myturn',
    'estimate',
    'bestmove',
))


def is_leaf_node(node):
    return isinstance(node.internode, float)


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
    bestmove, est = internode_estimate(moves, myturn)
    return Internode(
        moves=moves,
        myturn=myturn,
        estimate=est,
        bestmove=bestmove
    )


def internode_estimate(moves, myturn):
    """Compute internode's estimate based on its children's estimates.

    So for this to work, the children's estimates must already have been computed.
    :return: (bestmove, estimate)
    """
    subestimates = tuple((move, node_estimate(subnode))
                         for move, subnode in moves.items())
    return (max if myturn else min)(subestimates, key=operator.itemgetter(1))


def check_eog(c_off, c_def, iattack):
    if c_off and c_def:
        return None
    elif not c_off and not c_def:
        # A draw
        return 0.5
    elif not c_off:
        return 1.0 if iattack else 0.0
    else:
        assert not c_def
        return 0.0 if iattack else 1.0


def build_decision_tree(offense_cards, defense_cards, iattack, levels):
    res = check_eog(offense_cards, defense_cards, iattack)
    if res is not None:
        return res

    if levels == 0:
        # Estimate my cards vs rival's cards
        p1, p2 = cardset_relation(offense_cards, defense_cards)
        return Node(
            offense_cards=offense_cards,
            defense_cards=defense_cards,
            iattack=iattack,
            internode=p1 if iattack else p2
        )

    return Node(
        offense_cards=offense_cards,
        defense_cards=defense_cards,
        iattack=iattack,
        internode=principal_internode(offense_cards, defense_cards, iattack, levels)
    )


def principal_internode(offense_cards, defense_cards, iattack, levels):
    # Terminology:
    #   c_off, c_def - cards of offensive and defensive players that
    # they have on the hands;
    #   t_off, t_def - cards on the table (already put).
    # Nodes within this strike: {(t_off, t_def): Internode}
    internodes = {}

    def offensive(c_off, c_def, t_off, t_def):
        if (t_off, t_def) in internodes:
            return internodes[t_off, t_def]

        res = check_eog(c_off, c_def, iattack)
        if res is not None:
            internodes[t_off, t_def] = res
            return res

        if t_off:
            cards = matching_by_value(c_off, values_of(chain(t_off, t_def)))
        else:
            cards = c_off
        moves = {
            c: defensive(c_off - {c}, c_def, t_off | {c}, t_def, c)
            for c in cards
        }
        if t_off:
            moves[None] = make_subnode(t_off, t_def)
        node = make_internode(moves, iattack)
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
        node = make_internode(moves, not iattack)
        internodes[t_off, t_def] = node
        return node

    def put_unbeatables(c_off, c_def, t_off, t_def):
        assert len(t_off) == len(t_def) + 1
        assert len(c_def) >= 1

        if (t_off, t_def) in internodes:
            return internodes[t_off, t_def]

        more_cards = matching_by_value(c_off, values_of(chain(t_off, t_def)))
        n = min(len(c_def) - 1, len(more_cards))
        moves = {
            frozenset(cards): make_subnode(t_off.union(cards), t_def)
            for nn in range(n+1)
            for cards in combinations(more_cards, nn)
        }
        node = make_internode(moves, iattack)
        internodes[t_off, t_def] = node
        return node

    def make_subnode(t_off, t_def):
        assert len(t_off) >= len(t_def)
        if len(t_off) > len(t_def):
            return build_decision_tree(
                offense_cards - t_off,
                defense_cards | t_off,
                iattack,
                levels - 1
            )
        else:
            return build_decision_tree(
                defense_cards - t_def,
                offense_cards - t_off,
                not iattack,
                levels - 1
            )

    return offensive(offense_cards, defense_cards, frozenset(), frozenset())


MAXDEPTH = 3


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


def tree_count(node):
    if isinstance(node, Node):
        return tree_count(node.internode)
    if isinstance(node, Internode):
        return 1 + sum(tree_count(x) for x in node.moves.values())
    return 1


def deepen(node, lvl=0):
    def deepen_internode(intnd, lvl):
        #print('deepen', lvl)
        assert isinstance(intnd, Internode)
        for sub in intnd.moves.values():
            if isinstance(sub, Internode):
                deepen_internode(sub, lvl+1)
            elif isinstance(sub, Node):
                deepen(sub, lvl+1)
            else:
                assert isinstance(sub, float)

        bestmove, est = internode_estimate(intnd.moves, intnd.myturn)
        intnd.bestmove = bestmove
        intnd.estimate = est

    assert isinstance(node, Node)
    if is_leaf_node(node):
        node.internode = principal_internode(
            node.offense_cards,
            node.defense_cards,
            node.iattack,
            1
        )
    else:
        deepen_internode(node.internode, lvl+1)
