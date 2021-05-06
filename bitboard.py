import numpy as np
from constants import *


class Bitboard:
    def __init__(self):
        self.pieces_bb = np.zeros((2, 6), dtype=np.uint64)  # 2 sides, 6 piece bitboards per side
        self.combined_color = np.zeros(2, dtype=np.uint64)  # Combined bitboard for all pieces of given side
        self.combined_all = np.uint64(0)  # Combined bitboard for all pieces on the board
        self.color = Color.WHITE  # Color to move
        self.castling_flags = None
        self.en_passant_sq = None
        self.fifty_move_counter = 0

    def __str__(self):
        board_str = ""
        for r in reversed(Rank):
            for f in File:
                sq = Square.from_position(r, f)
                white_piece = self.piece_on(sq, Color.WHITE)
                if white_piece is not None:
                    board_str += str_pieces[white_piece.to_char().upper()]
                else:
                    black_piece = self.piece_on(sq, Color.BLACK)
                    if black_piece is not None:
                        board_str += str_pieces[black_piece.to_char()]
                    else:
                        board_str += '·'
            board_str += '\n'
        info_str = f"{self.color.name} to move"
        return f"{board_str}\n{info_str}"

    def get_piece_bb(self, piece, color=None):
        if not color:
            color = self.color
        return self.pieces[color][piece]

    def piece_on(self, sq, color=None):
        if not color:
            color = self.color
        return next((p for p in Piece if is_set(self.get_piece_bb(p, color), sq)), None)

    def init_game(self):
        self.pieces[Color.WHITE][Piece.PAWN] = np.uint64(0x000000000000FF00)
        self.pieces[Color.WHITE][Piece.KNIGHT] = np.uint64(0x0000000000000042)
        self.pieces[Color.WHITE][Piece.BISHOP] = np.uint64(0x0000000000000024)
        self.pieces[Color.WHITE][Piece.ROOK] = np.uint64(0x0000000000000081)
        self.pieces[Color.WHITE][Piece.QUEEN] = np.uint64(0x0000000000000008)
        self.pieces[Color.WHITE][Piece.KING] = np.uint64(0x0000000000000010)

        self.pieces[Color.BLACK][Piece.PAWN] = np.uint64(0x00FF000000000000)
        self.pieces[Color.BLACK][Piece.KNIGHT] = np.uint64(0x4200000000000000)
        self.pieces[Color.BLACK][Piece.BISHOP] = np.uint64(0x2400000000000000)
        self.pieces[Color.BLACK][Piece.ROOK] = np.uint64(0x8100000000000000)
        self.pieces[Color.BLACK][Piece.QUEEN] = np.uint64(0x0800000000000000)
        self.pieces[Color.BLACK][Piece.KING] = np.uint64(0x1000000000000000)

        for p in Piece:
            for c in Color:
                self.combined_color[c] |= self.pieces[c][p]

        self.combined_all = self.combined_color[Color.WHITE] | self.combined_color[Color.BLACK]


def is_set(bb, sq):
    return (sq.to_bitboard() & bb) != EMPTY_BB


bb = Bitboard()
bb.init_game()

sq = Square.from_position(Rank.SEVEN, File.B)

print(bb)

print([p for p in Piece if is_set(bb.get_piece_bb(p, Color.BLACK), sq)])
