from itertools import chain


def to_frozenset(obj):
    """If obj is a (frozen)set, return it.  Otherwise, feed to frozenset"""
    if isinstance(obj, (set, frozenset)):
        return obj
    else:
        return frozenset(obj)


RECORDTYPE_TEMPLATE = '''
class {typename}:
  __slots__ = ({slots})

  def __init__(self, {params}):
    {initbody}
'''


def recordtype(name, slotspec):
    nodefault = object()
    params = []
    for spec in slotspec:
        if isinstance(spec, tuple) and len(spec) == 2:
            params.append(spec)
        elif isinstance(spec, str):
            params.append((spec, nodefault))
        else:
            raise RuntimeError("Invalid slot spec: {}".format(spec))

    text = RECORDTYPE_TEMPLATE.format(
        typename=name,
        slots=','.join(map(lambda p: "'{}'".format(p[0]), params)),
        params=','.join(chain(
            (param for param, default in params if default is nodefault),
            ('{}={}'.format(param, default)
             for param, default in params
             if default is not nodefault)
        )),
        initbody='; '.join(
            'self.{slot} = {slot}'.format(slot=slot)
            for slot, default in params
        )
    )

    loc = {}
    exec(text, None, loc)
    return loc.popitem()[1]


def best_dict_pair(dct, better):
    bestv = bestk = first = object()
    for k, v in dct.items():
        if bestk is first or better(v, bestv):
            bestk = k
            bestv = v

    return bestk, bestv


def maxitem(iterable, key):
    bestvalue = bestitem = initial = object()
    for item in iterable:
        value = key(item)
        if bestitem is initial or value > bestvalue:
            bestitem, bestvalue = item, value
    assert bestitem is not initial

    return bestitem, bestvalue
