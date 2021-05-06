from enum import IntEnum
import numpy as np


class Color(IntEnum):
    WHITE = 0
    BLACK = 1

    def __invert__(self):
        if self == Color.WHITE:
            return Color.BLACK
        else:
            return Color.WHITE


class Piece(IntEnum):
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5

    def to_char(self):
        if self == Piece.PAWN:
            return 'p'
        elif self == Piece.KNIGHT:
            return 'n'
        elif self == Piece.BISHOP:
            return 'b'
        elif self == Piece.ROOK:
            return 'r'
        elif self == Piece.QUEEN:
            return 'q'
        elif self == Piece.KING:
            return 'k'


class Rank(IntEnum):
    ONE = 0
    TWO = 1
    THREE = 2
    FOUR = 3
    FIVE = 4
    SIX = 5
    SEVEN = 6
    EIGHT = 7


class File(IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7


class Square(object):
    def __init__(self, index):
        self.index = np.uint8(index)

    def __str__(self):
        r = self.index // 8
        f = self.index % 8
        return "%s%d" % (chr(ord('A')+f), 1+r)

    @classmethod
    def from_position(cls, r, f):
        return cls((r.value << np.uint8(3)) | f.value) # 8*rank + file

    @classmethod
    def from_str(cls, st):
        f = np.uint8(ord(st[0]) - ord('A'))
        r = np.uint8(int(st[1]) - 1)
        return cls((r << np.uint8(3)) | f) # 8*rank + file

    def to_bitboard(self):
        return np.uint64(1) << self.index


str_pieces = {'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟',
              'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙', '.': '·'}


# May want to move this to tables.py
EMPTY_BB = np.uint64(0)

# Clever bit manipulation wizardry to count trailing/leading zeros
# See https://www.chessprogramming.wikispaces.com/BitScan#Bitscan forward-De Bruijn Multiplication-With Isolated LS1B
# NOTE: only works if bb is non-zero
debruijn = np.uint64(0x03f79d71b4cb0a89)

lsb_lookup = np.array(
    [0, 1, 48, 2, 57, 49, 28, 3,
     61, 58, 50, 42, 38, 29, 17, 4,
     62, 55, 59, 36, 53, 51, 43, 22,
     45, 39, 33, 30, 24, 18, 12, 5,
     63, 47, 56, 27, 60, 41, 37, 16,
     54, 35, 52, 21, 44, 32, 23, 11,
     46, 26, 40, 15, 34, 20, 31, 10,
     25, 14, 19, 9, 13, 8, 7, 6],
    dtype=np.uint8)

msb_lookup = np.array(
    [0, 47, 1, 56, 48, 27, 2, 60,
     57, 49, 41, 37, 28, 16, 3, 61,
     54, 58, 35, 52, 50, 42, 21, 44,
     38, 32, 29, 23, 17, 11, 4, 62,
     46, 55, 26, 59, 40, 36, 15, 53,
     34, 51, 20, 43, 31, 22, 10, 45,
     25, 39, 14, 33, 19, 30, 9, 24,
     13, 18, 8, 12, 7, 6, 5, 63],
    dtype=np.uint8)


