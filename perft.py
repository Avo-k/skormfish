import time
from chess_logic import *
from tqdm import tqdm


def perft(pos, depth):
    if depth == 0:
        return 1
    count = 0
    moves = pos.gen_legal_moves()
    for m in tqdm(moves):
        count += child_perft(m[1], depth - 1)
    return count


def child_perft(pos, depth):
    if depth == 0:
        return 1
    count = 0
    moves = pos.gen_legal_moves()
    for m in moves:
        count += child_perft(m[1], depth - 1)
    return count


pos1 = Position(initial, 0, (True, True), (True, True), 0, 0)
time1 = {1: 20, 2: 400, 3: 8902, 4: 197281, 5: 4865609}
pos2 = parseFEN("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
time2 = {1: 48, 2: 2039, 3: 97862, 4: 4085603, 5: 193690690}
pos3 = parseFEN("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
time3 = {1: 14, 2: 191, 3: 2812, 4: 43238, 5: 674624}

positions = [(pos1, time1), (pos2, time2), (pos3, time3)]


def main():
    for i, (pos, t) in enumerate(positions, 1):
        print("-" * 30)
        print(" " * 8, f"POSITION {i}")
        print("-" * 30)

        for depth, result in t.items():
            # if depth == 5:
            #     break
            s = time.time()
            r = perft(pos, depth)
            assert r == result
            spent = (time.time() - s)
            print(f"depth {depth}: {round(r/spent, 2)} n/s")
            print(f"time spent {spent}")

import sys

if __name__ == "__main__":
    main()
