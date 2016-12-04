import os
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor

import gcxt
from dumb import scenario as dumb_scenario
from smart import scenario as smart_scenario
from smartest import scenario as smartest_scenario
from common import random_deck, NCARDS_PLAYER
from game import rungame


def launch_parallel(N):
    with ProcessPoolExecutor() as exe:
        M = N
        chunk = N // os.cpu_count()
        futures = []
        while M > 0:
            futures.append(exe.submit(launch_n_tasks, chunk, M == N))
            M -= chunk

    results = [x for f in futures for x in f.result()]
    print('total futures', len(futures))
    w1 = sum(1 for r in results if r is True)
    w2 = sum(1 for r in results if r is False)
    d = sum(1 for r in results if r is None)

    print("Results: ", w1, d, w2)


def launch_n_tasks(N, doprint=False):
    res = []
    for i in range(N):
        res.append(launch_1_game())
        if doprint and i % 1000 == 0:
            print(i, "processed")
    return res


def launch_in_1_process(N):
    results = []

    for i in range(N):
        results.append(launch_1_game())
        #print(i, "processed")
        if i % 1000 == 0:
            print(i, "processed")

    w1 = sum(1 for r in results if r is True)
    w2 = sum(1 for r in results if r is False)
    d = sum(1 for r in results if r is None)
    print("Results: ", w1, d, w2)


def launch_1_game():
    return rungame(
        smartest_scenario,
        dumb_scenario,
    )


def main():
    parser = ArgumentParser()
    parser.add_argument('N', type=int)
    args = parser.parse_args()
    #launch_in_1_process(args.N)
    launch_parallel(args.N)


if __name__ == '__main__':
    main()
    # for _ in range(10):
    #     example()
