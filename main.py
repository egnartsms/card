from argparse import ArgumentParser
from functools import partial
from concurrent.futures import ProcessPoolExecutor, wait
from random import seed

import gcxt
from game import rungame
from dumb import play as play_dumb
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


# def launch_in_1_process(N):
#     results = [launch_1_game() for i in range(N)]
#     w1 = sum(1 for r in results if r is True)
#     w2 = sum(1 for r in results if r is False)
#     d = sum(1 for r in results if r is None)
#     print("Results: ", w1, d, w2)


# def launch_1_game():
#     return play(partial(DumbPlayer, {'put-more-trumps': True,
#                                      'choose-card': 'min'}),
#                 partial(SmartPlayer))


def main():
    # launch_1_game()
    # return
    seed(212)
    res = rungame(
        partial(play_dumb, options={'put-more-trumps': True,
                                    'choose-card': 'min'}),
        partial(play_dumb, options={'put-more-trumps': True,
                                    'choose-card': 'min'})
    )
    print(res)
    return

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
