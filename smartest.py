from common import RequestCode as rc
from decision_tree import build_decision_tree, Internode, deepen, tree_count
from smart import scenario as smart_scenario


def scenario(send, cards, iattack):
    return smart_scenario(send, cards, iattack, decision_scenario)


MAX_LEVELS = 3


def decision_scenario(send, coff, cdef, iattack):
    def offense(intnd):
        """Return next Node"""
        #print("i offense")
        while isinstance(intnd, Internode):
            offcard = intnd.bestmove
            send(offcard)
            #print("offcard", offcard)
            if offcard is None or isinstance(offcard, frozenset):
                return intnd.moves[offcard]
            defcard = yield rc.DEFCARD
            #print("defcard", defcard)
            intnd = intnd.moves[offcard].moves[defcard]
        return intnd

    def defense(intnd):
        """Return next Node"""
        #print("i defense")
        while isinstance(intnd, Internode):
            offcard = yield rc.OFFCARD
            #print("offcard", offcard)
            if offcard is None or isinstance(offcard, frozenset):
                return intnd.moves[offcard]
            defcard = intnd.moves[offcard].bestmove
            send(defcard)
            #print("defcard", defcard)
            intnd = intnd.moves[offcard].moves[defcard]
            if defcard is None:
                return intnd.moves[(yield rc.UNBEATABLES)]
        return intnd

    print("Building tree..")
    root = build_decision_tree(coff, cdef, iattack, MAX_LEVELS)
    print("Done, count is", tree_count(root))

    while True:
        #print("off", root.offense_cards, "against", root.defense_cards)
        if root.iattack:
            next_node = (yield from offense(root.internode))
        else:
            next_node = (yield from defense(root.internode))

        yield rc.REPLENISHMENT
        yield rc.NUM_RIVAL_REPLENISHMENT

        if isinstance(next_node, float):
            print("next_node is ", next_node, "quitting")
            break

        root = next_node
        tc = tree_count(root)
        if tc < 5000:
            print("Count is", tc, "deepening..")
            deepen(root)
            print("Done, count is", tree_count(root))
        else:
            print("Count is", tc, "decided not to deepen")
