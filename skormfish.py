from chess_logic import *
import time


class Skormfish:
    def __init__(self, time_limit=5, print_infos=False):
        self.tt = {}
        self.tt_move = {}
        self.tt_score = {}
        self.hist = [Position(initial, 0, (True, True), (True, True), 0, 0)]
        self.time_limit = time_limit
        self.nodes = 0
        self.tt_cutoff = 0
        self.print_infos = print_infos

    def search(self, pos, alpha=float('-inf'), beta=float('inf')):
        """Iterative-deepening"""
        self.nodes = self.tt_cutoff = 0
        self.tt_score.clear()
        print(pos.pst())

        for depth in range(1, 1000):
            self.negamax(pos, -beta, -alpha, depth)
            yield depth, self.tt_move.get(pos), self.tt_score.get((pos, depth, True)).value

    def pondering(self, pos, alpha=float('-inf'), beta=float('inf')):
        pass

    def negamax(self, pos, alpha, beta, depth, root=True):
        """Negamax search with A/B pruning and transposition tables"""
        self.nodes += 1
        depth = max(depth, 0)
        if pos.score <= -MATE_LOWER:
            return -MATE_UPPER
        if not root and self.hist.count(pos) >= 2:
            return 0

        alphaorig = alpha
        ttentry = self.tt_score.get((pos, depth, root))
        if ttentry:
            self.tt_cutoff += 1
            if ttentry.flag == "pv":  # exact
                return ttentry.value
            elif ttentry.flag == "all":  # upper
                alpha = max(alpha, ttentry.value)
            elif ttentry.flag == "cut":  # lower
                beta = min(beta, ttentry.value)

            if alpha >= beta:
                return ttentry.value

        def moves():
            """generator to yield moves in order"""
            if depth > 0 and not root and any(c in pos.board for c in 'RBNQ'):
                yield None, -self.negamax(pos.nullmove(), -beta, -alpha, depth - 3, False)
            if depth == 0:
                yield None, pos.score

            killer = self.tt_move.get(pos)
            if killer and (depth > 0 or pos.value(killer) >= QS_LIMIT):
                yield killer, -self.negamax(pos.move(killer), -beta, -alpha, depth - 1, False)

            for _move in sorted(pos.gen_moves(), key=pos.value, reverse=True):
                if depth > 0 or pos.value(_move) >= QS_LIMIT:
                    yield _move, -self.negamax(pos.move(_move), -beta, -alpha, depth - 1, False)

        value = float('-inf')
        move = None
        for m, v in moves():
            if v > value:
                value = v
                move = m
            alpha = max(alpha, value)
            if alpha >= beta:
                break  # prune the branch

        if len(self.tt_move) > TABLE_SIZE: self.tt_move.clear()
        self.tt_move[pos] = move

        if value < 0 < depth:
            is_dead = lambda pos: any(pos.value(m) >= MATE_LOWER for m in pos.gen_moves())
            if all(is_dead(pos.move(m)) for m in pos.gen_moves()):
                in_check = is_dead(pos.nullmove())
                value = -MATE_UPPER if in_check else 0

        if value <= alphaorig:
            flag = "all"
        elif value >= beta:
            flag = "cut"
        else:
            flag = "pv"
        if len(self.tt_score) > TABLE_SIZE: self.tt_score.clear()
        self.tt_score[pos, depth, root] = Entry(flag, value)

        return value

    def play(self, fen=None, pos=None):
        if not pos:
            pos = parseFEN(fen)
        self.hist.append(pos)
        depth = move = score = None
        start = time.time()

        for depth, move, score in self.search(pos):
            if time.time() - start > self.time_limit:
                break

        self.hist.append(pos.move(move))
        move = mrender(pos, move)

        if self.print_infos:
            print(f" move: {move} - score: {score}\n",
                  f"depth: {depth} - time: {round(time.time() - start, 2)}\n",
                  f"nodes: {self.nodes} - tt_cutoff: {self.tt_cutoff} \n",
                  "-"*40)
        return move

    def from_moves(self, moves):
        """update self.hist with a list of uci moves"""
        moves = moves.split()
        c = False
        for move in moves[:-1]:
            self.hist.append(self.hist[-1].move(mparse(c, move)))
            c = not c

    def from_pos(self, fen):
        """append a FEN to self.hist"""
        pos = parseFEN(fen)
        self.hist.append(pos)
