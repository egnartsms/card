import os
from argparse import ArgumentParser
from functools import partial
from concurrent.futures import ProcessPoolExecutor

import gcxt
from dumb import scenario as dumb_scenario
from smart import scenario as smart_scenario
from common import random_deck, NCARDS_PLAYER
from game import rungame
from decision_tree import build_decision_tree, tree_count


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
        #print(i)
        if i % 1000 == 0:
            print(i, "processed")

    w1 = sum(1 for r in results if r is True)
    w2 = sum(1 for r in results if r is False)
    d = sum(1 for r in results if r is None)
    print("Results: ", w1, d, w2)


def launch_1_game():
    return rungame(
        dumb_scenario,
        dumb_scenario
    )


def main():
    parser = ArgumentParser()
    parser.add_argument('N', type=int)
    args = parser.parse_args()
    #launch_in_1_process(args.N)
    launch_parallel(args.N)


def example():
    deck = random_deck()
    gcxt.trump = 'spades'
    node = build_decision_tree(
        frozenset(deck[:NCARDS_PLAYER]),
        frozenset(deck[NCARDS_PLAYER:2*NCARDS_PLAYER]),
        True,
        3
    )
    print("Count is", tree_count(node))


def C(n, m):
    de_g, de_l = m, n - m
    if de_g < de_l:
        de_g, de_l = de_l, de_g
    res, k = 1, n
    while k > de_g:
        res *= k
        k -= 1
    k = 1
    while k <= de_l:
        res //= k
        k += 1

    return res


def total():
    def subsum(n):
        return sum(C(n, i) for i in range(1, 6+1))

    return sum(C(36, i) * subsum(36 - i) for i in range(1, 6+1))


def final():
    n = total()
    return n // 24


if __name__ == '__main__':
    #main()
    for _ in range(30):
        example()
    pass
