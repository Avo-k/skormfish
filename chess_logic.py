from __future__ import print_function
from itertools import count
from collections import namedtuple
import re, sys, time

# TODO: mobility, opp/end piece value/pst, BNR pairs, King safety


WHITE, BLACK = range(2)
FEN_INITIAL = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

opp_piece_value = {'P': 100, 'N': 305, 'B': 333, 'R': 563, 'Q': 950, 'K': 60000}
end_piece_value = {'P': 125, 'N': 280, 'B': 360, 'R': 600, 'Q': 1000, 'K': 60000}

opp_pst = {
    'P':   ( 0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
             5,  5, 10, 25, 25, 10,  5,  5,
             0,  0,  0, 20, 20,  0,  0,  0,
             5, -5,-10,  0,  0,-10, -5,  5,
             5, 10, 10,-20,-20, 10, 10,  5,
             0,  0,  0,  0,  0,  0,  0,  0),

    'N':   (-50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50),

    'B':   (-20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20),

    'R':    ( 0,  0,  0,  0,  0,  0,  0,  0,
              5, 10, 10, 10, 10, 10, 10,  5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
              0,  0,  0,  5,  5,  0,  0,  0),

    'Q':   (-20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
             -5,  0,  5,  5,  5,  5,  0, -5,
              0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20),

    'K':   (-30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
             20, 20,  0,  0,  0,  0, 20, 20,
             20, 30, 10,  0,  0, 10, 30, 20)
}

end_pst = opp_pst.copy()

end_pst['K'] = (-50,-40,-30,-20,-20,-30,-40,-50,
                -30,-20,-10,  0,  0,-10,-20,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-30,  0,  0,  0,  0,-30,-30,
                -50,-30,-30,-30,-30,-30,-30,-50)

end_pst['P'] = ( 0,  0,  0,  0,  0,  0,  0,  0,
                80, 80, 80, 80, 80, 80, 80, 80,
                20, 20, 30, 40, 40, 30, 20, 20,
                10, 10, 15, 30, 30, 15, 10, 10,
                 5,  5, 10, 20, 20, 10,  5,  5,
                 0,-10,-15, -5, -5,-15,-10,  0,
                -5, -5, -5,-20,-20, -5, -5, -5,
                 0,  0,  0,  0,  0,  0,  0,  0)


def pad_n_join(piece_value, pst):
    for k, table in pst.items():
        padrow = lambda row: (0,) + tuple(x + piece_value[k] for x in row) + (0,)
        pst[k] = sum((padrow(table[i * 8:i * 8 + 8]) for i in range(8)), ())
        pst[k] = (0,) * 20 + opp_pst[k] + (0,) * 20
    return pst


# pad and join both piece square tables
opp_pst = pad_n_join(opp_piece_value, opp_pst)
end_pst = pad_n_join(end_piece_value, end_pst)

# Our board is represented as a 120 character string. The padding allows for
# fast detection of moves that don't stay within the board.
A1, H1, A8, H8 = 91, 98, 21, 28
initial = (
    '         \n'  # 0 -  9
    '         \n'  # 10 - 19
    ' rnbqkbnr\n'  # 20 - 29
    ' pppppppp\n'  # 30 - 39
    ' ........\n'  # 40 - 49
    ' ........\n'  # 50 - 59
    ' ........\n'  # 60 - 69
    ' ........\n'  # 70 - 79
    ' PPPPPPPP\n'  # 80 - 89
    ' RNBQKBNR\n'  # 90 - 99
    '         \n'  # 100 -109
    '         \n'  # 110 -119
)

# Lists of possible moves for each piece type.
N, E, S, W = -10, 1, 10, -1
directions = {
    'P': (N, N + N, N + W, N + E),
    'N': (N + N + E, E + N + E, E + S + E, S + S + E, S + S + W, W + S + W, W + N + W, N + N + W),
    'B': (N + E, S + E, S + W, N + W),
    'R': (N, E, S, W),
    'Q': (N, E, S, W, N + E, S + E, S + W, N + W),
    'K': (N, E, S, W, N + E, S + E, S + W, N + W)
}

# When a MATE is detected, we'll set the score to MATE_UPPER - plies to get there
# E.g. Mate in 3 will be MATE_UPPER - 6
MATE_LOWER = opp_piece_value['K'] - 10 * opp_piece_value['Q']
MATE_UPPER = opp_piece_value['K'] + 10 * opp_piece_value['Q']

# transposition table max len
TABLE_SIZE = 1e7

# Delta pruning
QS_LIMIT = 200


def get_color(pos):
    ''' A slightly hacky way to to get the color from a sunfish position '''
    return BLACK if pos.board.startswith('\n') else WHITE

# lower <= s(pos) <= upper
Entry = namedtuple('Entry', 'flag value')

#####################################################
# The Board
#####################################################

class Position(namedtuple('Position', 'board score wc bc ep kp')):
    """ A state of a chess game
    board -- a 120 char representation of the board
    score -- the board evaluation
    wc -- the castling rights, [west/queen side, east/king side]
    bc -- the opponent castling rights, [west/king side, east/queen side]
    ep - the en passant square
    kp - the king passant square
    """

    def gen_moves(self):
        # For each of our pieces, iterate through each possible 'ray' of moves,
        # as defined in the 'directions' map. The rays are broken e.g. by
        # captures or immediately in case of pieces such as knights.
        for i, p in enumerate(self.board):
            if not p.isupper(): continue
            for d in directions[p]:
                for j in count(i + d, d):
                    q = self.board[j]
                    # Stay inside the board, and off friendly pieces
                    if q.isspace() or q.isupper(): break
                    # Pawn move, double move and capture
                    if p == 'P' and d in (N, N + N) and q != '.': break
                    if p == 'P' and d == N + N and (i < A1 + N or self.board[i + N] != '.'): break
                    if p == 'P' and d in (N + W, N + E) and q == '.' \
                            and j not in (self.ep, self.kp, self.kp - 1, self.kp + 1): break
                    # Move it
                    yield (i, j)
                    # Stop crawlers from sliding, and sliding after captures
                    if p in 'PNK' or q.islower(): break
                    # Castling, by sliding the rook next to the king
                    if i == A1 and self.board[j + E] == 'K' and self.wc[0]: yield (j + E, j + W)
                    if i == H1 and self.board[j + W] == 'K' and self.wc[1]: yield (j + W, j + E)

    def rotate(self):
        ''' Rotates the board, preserving enpassant '''
        return Position(
            self.board[::-1].swapcase(), -self.score, self.bc, self.wc,
            119 - self.ep if self.ep else 0,
            119 - self.kp if self.kp else 0)

    def nullmove(self):
        ''' Like rotate, but clears ep and kp '''
        return Position(
            self.board[::-1].swapcase(), -self.score,
            self.bc, self.wc, 0, 0)

    def move(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        put = lambda board, i, p: board[:i] + p + board[i + 1:]
        # Copy variables and reset ep and kp
        board = self.board
        wc, bc, ep, kp = self.wc, self.bc, 0, 0
        score = self.score + self.value(move)
        # Actual move
        board = put(board, j, board[i])
        board = put(board, i, '.')
        # Castling rights, we move the rook or capture the opponent's
        if i == A1: wc = (False, wc[1])
        if i == H1: wc = (wc[0], False)
        if j == A8: bc = (bc[0], False)
        if j == H8: bc = (False, bc[1])
        # Castling
        if p == 'K':
            wc = (False, False)
            if abs(j - i) == 2:
                kp = (i + j) // 2
                board = put(board, A1 if j < i else H1, '.')
                board = put(board, kp, 'R')
        # Pawn promotion, double move and en passant capture
        if p == 'P':
            if A8 <= j <= H8:
                board = put(board, j, 'Q')
            if j - i == 2 * N:
                ep = i + N
            if j == self.ep:
                board = put(board, j + S, '.')
        # We rotate the returned position, so it's ready for the next player
        return Position(board, score, wc, bc, ep, kp).rotate()

    def value(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        # Actual move
        score = opp_pst[p][j] - opp_pst[p][i]
        # Capture
        if q.islower():
            score += opp_pst[q.upper()][119 - j]
        # Castling check detection
        if abs(j - self.kp) < 2:
            score += opp_pst['K'][119 - j]
        # Castling
        if p == 'K' and abs(i - j) == 2:
            score += opp_pst['R'][(i + j) // 2]
            score -= opp_pst['R'][A1 if j < i else H1]
        # Special pawn stuff
        if p == 'P':
            if A8 <= j <= H8:
                score += opp_pst['Q'][j] - opp_pst['P'][j]
            if j == self.ep:
                score += opp_pst['P'][119 - (j + S)]
        return score


#####################################################
# Parse and render
#####################################################


def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1]) - 1
    return A1 + fil - 10 * rank


def render(i):
    rank, fil = divmod(i - A1, 10)
    return chr(fil + ord('a')) + str(-rank + 1)


def mrender(pos, m):
    """sunfish to uci"""
    # Sunfish always assumes promotion to queen
    p = 'q' if A8 <= m[1] <= H8 and pos.board[m[0]] == 'P' else ''
    m = m if get_color(pos) == WHITE else (119 - m[0], 119 - m[1])
    return render(m[0]) + render(m[1]) + p


def mparse(color, move):
    """uci to sunfish"""
    m = (parse(move[0:2]), parse(move[2:4]))
    return m if color == WHITE else (119 - m[0], 119 - m[1])


def parseFEN(fen):
    """ Parses a string in Forsyth-Edwards Notation into a Position """
    board, color, castling, enpas, _hclock, _fclock = fen.split()
    board = re.sub(r'\d', (lambda m: '.' * int(m.group(0))), board)
    board = list(21 * ' ' + '  '.join(board.split('/')) + 21 * ' ')
    board[9::10] = ['\n'] * 12
    # if color == 'w': board[::10] = ['\n']*12
    # if color == 'b': board[9::10] = ['\n']*12
    board = ''.join(board)
    wc = ('Q' in castling, 'K' in castling)
    bc = ('k' in castling, 'q' in castling)
    ep = parse(enpas) if enpas != '-' else 0
    score = sum(opp_pst[p][i] for i, p in enumerate(board) if p.isupper())
    score -= sum(opp_pst[p.upper()][119 - i] for i, p in enumerate(board) if p.islower())
    pos = Position(board, score, wc, bc, ep, 0)
    return pos if color == 'w' else pos.rotate()


def print_pos(pos):
    print()
    uni_pieces = {'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟',
                  'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙', '.': '·'}
    for i, row in enumerate(pos.board.split()):
        print(' ', 8 - i, ' '.join(uni_pieces.get(p, p) for p in row))
    print('    a b c d e f g h \n\n')
