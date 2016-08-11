import os
from argparse import ArgumentParser
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import gcxt
from dumb import scenario as dumb_scenario
from game import rungame


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
        partial(dumb_scenario, options={'put-more-trumps': True,
                                        'choose-card': 'min'}),
        partial(dumb_scenario, options={'put-more-trumps': True,
                                        'choose-card': 'min'})
    )


def main():
    parser = ArgumentParser()
    parser.add_argument('N', type=int)
    args = parser.parse_args()
    launch_in_1_process(args.N)
    #launch_parallel(args.N)


def example():
    from common import random_deck, random_suit, NCARDS_PLAYER
    from decision_tree import build_tree, tree_count

    for i in range(10):
        gcxt.trump = random_suit()
        deck = random_deck()
        node = build_tree(
            deck[:NCARDS_PLAYER],
            deck[NCARDS_PLAYER:2 * NCARDS_PLAYER],
            True,
        )
        print(tree_count(node))


if __name__ == '__main__':
    #main()
    example()
