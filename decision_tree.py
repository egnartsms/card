from operator import itemgetter
from itertools import combinations, chain, groupby
from contextlib import wraps
from functools import partial

from common import beats, matching_by_value, values_of, card_value, unbeatables


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


def cache_results_in(mapping):
    def decorator(fn):
        @wraps(fn)
        def wrapper(c_off, c_def, t_off, t_def, *rest):
            if (t_off, t_def) in mapping:
                return mapping[t_off, t_def]
            result = fn(c_off, c_def, t_off, t_def, *rest)
            assert isinstance(result, tuple) and len(result) == 2
            mapping[t_off, t_def] = result
            return result
        return wrapper
    return decorator


def make_decision(levels, fn):
    # Terminology:
    #   c_off, c_def - cards of offensive and defensive players that
    # they have on the hands;
    #   t_off, t_def - cards on the table (already put).

    outcomes = {}  # (toff, tdef) -> (estimate, bestmove)
    nextlevel = partial(make_offense_decision, levels - 1)

    @cache_results_in(outcomes)
    def i_attack(c_off, c_def, t_off, t_def):
        res = check_eog(c_off, c_def, True)
        if res is not None:
            return res, None
        if t_off:
            suitable = matching_by_value(c_off, values_of(t_off | t_def))
        else:
            suitable = c_off

        variants = [(rival_defends(c_off - {c}, c_def, t_off | {c}, t_def, c)[0], c)
                    for c in suitable]
        if t_off:
            variants.append((nextlevel(c_def, c_off, False)[0], None))
        return max(variants, key=itemgetter(0))

    @cache_results_in(outcomes)
    def rival_defends(c_off, c_def, t_off, t_def, offcard):
        assert offcard in t_off
        assert offcard not in c_off
        assert len(t_off) == len(t_def) + 1
        assert c_def

        suitable = tuple(c for c in c_def if beats(c, offcard))
        if not suitable:
            return i_put_unbeatables(c_off, c_def, t_off, t_def)

        defcard = min(suitable, key=card_value)
        return i_attack(c_off, c_def - {defcard}, t_off, t_def | {defcard})

    @cache_results_in(outcomes)
    def i_put_unbeatables(c_off, c_def, t_off, t_def):
        suitable = matching_by_value(c_off, values_of(t_off | t_def))
        variants = [
            (
                nextlevel(c_off.difference(unb), c_def.union(t_off, t_def, unb), True)[0],
                frozenset(unb)
            )
            for n in range(min(len(suitable), len(c_def) - 1) + 1)
            for unb in combinations(suitable, n)
        ]
        return max(variants, key=itemgetter(0))

    @cache_results_in(outcomes)
    def rival_attacks(c_off, c_def, t_off, t_def):
        res = check_eog(c_off, c_def, False)
        if res is not None:
            return res, None
        if not t_off:
            offcard = min(c_off, key=card_value)
        else:
            suitable = matching_by_value(c_off, values_of(t_off | t_def))
            offcard = min(suitable, key=card_value) if suitable else None

        if offcard is None:
            return nextlevel(c_def, c_off, True)
        else:
            return i_defend(c_off - {offcard}, c_def, t_off | {offcard}, t_def, offcard)

    @cache_results_in(outcomes)
    def i_defend(c_off, c_def, t_off, t_def, offcard):
        assert offcard in t_off
        assert offcard not in c_off
        assert len(t_off) == len(t_def) + 1
        assert c_def

        suitable = tuple(c for c in c_def if beats(c, offcard))
        variants = [
            (rival_attacks(c_off, c_def - {c}, t_off, t_def | {c})[0], c)
            for c in suitable
        ]
        variants.append((rival_puts_unbeatables(c_off, c_def, t_off, t_def)[0], None))
        return max(variants, key=itemgetter(0))

    @cache_results_in(outcomes)
    def rival_puts_unbeatables(c_off, c_def, t_off, t_def):
        unb = unbeatables(c_off, values_of(t_off | t_def), len(c_def) - 1)
        return nextlevel(c_off - unb, c_def | t_off | t_def | unb, False)

    if fn == 'i_attack':
        return i_attack
    elif fn == 'i_defend':
        return i_defend
    elif fn == 'i_put_unbeatables':
        return i_put_unbeatables
    elif fn == 'rival_attacks':
        return rival_attacks


def make_offense_decision(levels, c_off, c_def, iattack):
    """Special case of `make_decision': simplified use"""
    if levels == 0:
        # Estimate my cards vs rival's cards
        p1, p2 = cardset_relation(c_off, c_def)
        return p1 if iattack else p2, None

    if iattack:
        fn = make_decision(levels, 'i_attack')
    else:
        fn = make_decision(levels, 'rival_attacks')

    return fn(c_off, c_def, frozenset(), frozenset())


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
        key=itemgetter(0),
        reverse=True
    )
    met1, met2 = 0, 0
    p1, p2 = 0, 0
    for key, cardgroup in groupby(cards, itemgetter(0)):
        values = tuple(map(itemgetter(1), cardgroup))
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
