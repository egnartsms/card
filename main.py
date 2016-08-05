import os
from argparse import ArgumentParser
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import gcxt
from dumb import Player as DumbPlayer
from game import rungame
#from smart1 import SmartPlayer
from common import Card


def launch_parallel(N):
    with ProcessPoolExecutor() as exe:
        M = N
        chunk = N // os.cpu_count()
        futures = []
        while M > 0:
            futures.append(exe.submit(launch_n_tasks, chunk))
            M -= chunk

    results = [x for f in futures for x in f.result()]
    print('total futures', len(futures))
    w1 = sum(1 for r in results if r is True)
    w2 = sum(1 for r in results if r is False)
    d = sum(1 for r in results if r is None)

    print("Results: ", w1, d, w2)


def launch_n_tasks(N):
    return [launch_1_game() for i in range(N)]


def launch_in_1_process(N):
    results = []

    for i in range(N):
        results.append(launch_1_game())
        if i % 1000 == 0:
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
    #launch_parallel(args.N)


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
