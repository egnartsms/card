from common import RequestCode as rc
from decision_tree import make_decision
from smart import scenario as smart_scenario


def scenario(send, cards, iattack):
    return smart_scenario(send, cards, iattack, decision_scenario)


MAX_LEVELS = 2


def decision_scenario(send, mycards, hiscards, iattack):
    def offense():
        """Conduct our offense. Params are mutable sets"""
        toff, tdef = set(), set()
        while mycards and hiscards:
            fn = make_decision(MAX_LEVELS, 'i_attack')
            est, offcard = fn(
                frozenset(mycards),
                frozenset(hiscards),
                frozenset(toff),
                frozenset(tdef)
            )
            send(offcard)
            if offcard is None:
                return False
            mycards.remove(offcard)
            toff.add(offcard)

            defcard = yield rc.DEFCARD
            if defcard is None:
                fn = make_decision(MAX_LEVELS, 'i_put_unbeatables')
                est, unb = fn(
                    frozenset(mycards),
                    frozenset(hiscards),
                    frozenset(toff),
                    frozenset(tdef)
                )
                send(unb)
                mycards.difference_update(unb)
                hiscards.update(unb, toff, tdef)
                return True
            hiscards.remove(defcard)
            tdef.add(defcard)

    def defense():
        """Conduct our defense. Params are mutable sets"""
        toff, tdef = set(), set()
        while mycards and hiscards:
            offcard = yield rc.OFFCARD
            if offcard is None:
                return True
            hiscards.remove(offcard)
            toff.add(offcard)

            fn = make_decision(MAX_LEVELS, 'i_defend')
            est, defcard = fn(
                frozenset(hiscards),
                frozenset(mycards),
                frozenset(toff),
                frozenset(tdef),
                offcard
            )
            send(defcard)
            if defcard is None:
                unb = yield rc.UNBEATABLES
                hiscards.difference_update(unb)
                mycards.update(unb, toff, tdef)
                return False

            mycards.remove(defcard)
            tdef.add(defcard)

    while mycards and hiscards:
        iattack = (yield from offense()) if iattack else (yield from defense())

        yield rc.REPLENISHMENT
        yield rc.NUM_RIVAL_REPLENISHMENT
