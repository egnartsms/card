from argparse import ArgumentParser
from functools import partial
from random import seed

import gcxt
from dumb import Player as DumbPlayer
from game import rungame
#from smart1 import SmartPlayer
from common import Card


# def launch(N):
#     with ProcessPoolExecutor(4) as exe:
#         futures = [exe.submit(launch_1_game) for i in range(N)]
#         wait(futures)
#         results = [f.result() for f in futures]
#         w1 = sum(1 for r in results if r is True)
#         w2 = sum(1 for r in results if r is False)
#         d = sum(1 for r in results if r is None)
#
#     print("Results: ", w1, d, w2)


def launch_in_1_process(N):
    results = []

    for i in range(N):
        results.append(launch_1_game())
        if i % 100 == 0:
            print(i, 'processed')

    w1 = sum(1 for r in results if r is True)
    w2 = sum(1 for r in results if r is False)
    d = sum(1 for r in results if r is None)
    print("Results: ", w1, d, w2)


def launch_1_game():
    return rungame(
        partial(DumbPlayer, options={'put-more-trumps': True,
                                     'choose-card': 'min'}),
        partial(DumbPlayer, options={'put-more-trumps': True,
                                     'choose-card': 'min'})
    )


def main():
    parser = ArgumentParser()
    parser.add_argument('N', type=int)
    args = parser.parse_args()
    launch_in_1_process(args.N)


def example():
    from decision_tree import build_tree, vis_tree_structure

    gcxt.trump = 'spades'
    tree = build_tree(
        frozenset([Card('spades', 9), Card('diamonds', 7), Card('hearts', 12)]),
        frozenset([Card('diamonds', 10), Card('clubs', 13), Card('hearts', 8)]),
        True,
    )
    vis = vis_tree_structure(tree)
    print(tree.estimate)


if __name__ == '__main__':
    main()
