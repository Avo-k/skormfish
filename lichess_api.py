import berserk
import time
import threading
import random

import skormfish as sk
from chess_logic import pv
import chess
import chess.polyglot

API_TOKEN = open("api_token.txt").read()
bot_id = 'skormfish'

session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

gl_quotes = ["May the force be with you", "gl hf", "Good luck\nhave fun"]
gg_quotes = ["There’s always a bigger fish", "gg", "Good game\nwell played",
             "You win.. This time"]


class Game:
    def __init__(self, client, game_id):
        self.game_id = game_id
        self.client = client
        self.stream = client.bots.stream_game_state(game_id)
        self.infos = next(self.stream)
        self.bot_white = self.infos['white'].get('id') == bot_id
        self.current_state = self.infos['state']
        self.ctime = "wtime" if self.bot_white else "btime"
        self.bot = sk.Skormfish()
        self.moves = ""
        self.ponder = None
        self.deltas = [0.0]
        self.print_infos = True
        self.theory = True

    def run(self):
        print('game start!')
        client.bots.post_message(game_id, random.choice(gl_quotes))

        # From Position
        if self.infos['variant']['short'] == "FEN":
            self.bot.from_pos(self.infos['initialFen'])
            if self.bot_white:
                self.make_first_move()

        # Reconnect to a game
        elif self.moves != self.current_state['moves']:
            self.bot.from_moves(self.current_state['moves'])
            self.handle_state_change(self.current_state)

        # if you have to start
        elif not self.current_state['moves'] and self.bot_white:
            self.make_first_move()

        # Game loop
        for event in self.stream:
            if event['type'] == 'gameState':
                if event['status'] == 'started':
                    self.handle_state_change(event)
                elif event['status'] in ('mate', 'resign', 'outoftime', 'aborted', 'draw'):
                    client.bots.post_message(game_id, random.choice(gg_quotes))
                    break
                else:
                    print('NEW', event['status'])
                    break
            elif event['type'] == 'chatLine':
                self.handle_chat_line(event)

    def handle_state_change(self, game_state):
        # If state change is not a move (draws offers, flag...)
        if game_state['moves'] == self.moves:
            return
        self.moves = game_state['moves']

        moves = game_state['moves'].split()
        color = not bool(len(moves) % 2)
        pos = self.bot.hist[-1].move(sk.mparse(color, moves[-1]))
        self.bot.hist.append(pos)
        bot_turn = self.bot_white == color
        depth = score = move = None

        # Time variables
        start = time.time()
        t = game_state[self.ctime]
        remaining_time = t / 1000 if isinstance(t, int) else t.minute * 60 + t.second

        if bot_turn:

            # Look in the books
            if self.theory:
                entry = self.ask_leela(moves)
                if entry:
                    self.client.bots.make_move(game_id, entry.move)
                    print("still theory")
                    return
                else:
                    self.theory = False
                    print("end of theory")
                    client.bots.post_message(game_id, f"*Agadmator's voice* And as of move {len(moves)} we have a "
                                                      f"completely new game")

            # Set limits
            time_limit = min(5, remaining_time / 60)
            depth_limit = max(5, remaining_time // 10)
            nodes_limit = time_limit * 8000

            # Look for a move
            for depth, move, score in self.bot.search(pos):
                # _moves = pv(self.bot, pos, include_scores=False)
                if time.time() - start > time_limit:
                    break
                if depth == depth_limit:
                    break
                if self.bot.nodes > nodes_limit:
                    break

            actual_time = time.time() - start

            # Play the move
            move = sk.mrender(pos, move)
            try:
                self.client.bots.make_move(game_id, move)
            except:  # Flagged!
                return

            self.deltas.append(round(actual_time - time_limit, 2))
            if self.print_infos:
                print("-" * 40)
                print(f"depth: {depth} - time: {round(actual_time, 2)} seconds")
                print(f"score: {score} - time delta: {round(actual_time - time_limit, 2)}")
                print(f"nodes: {self.bot.nodes} - n/s: {round(self.bot.nodes / actual_time)}")
                print(f"deltas means {round(sum(self.deltas) / len(self.deltas), 2)}")

        else:  # pondering
            pondering_depth = min(5, remaining_time // 10)
            if self.theory:
                pondering_depth = 4
            if pondering_depth < 2:
                return

            for depth, move, score in self.bot.search(pos):
                if depth == pondering_depth:
                    break

            actual_time = time.time() - start
            if self.print_infos:
                print("-" * 40)
                print(f"pondering: {depth}d {round(actual_time, 2)}s")

    @staticmethod
    def ask_leela(moves):
        leela = chess.polyglot.open_reader("opening_book/leelabook.bin")
        board = chess.Board()
        for m in moves:
            board.push_uci(m)
        return leela.get(board)

    def make_first_move(self):
        pos = self.bot.hist[-1]
        start = time.time()
        move = None
        for depth, move, score in self.bot.search(pos):
            if time.time() - start > 5:
                break
            if depth == 6:
                break
        # Play the move
        move = sk.mrender(pos, move)
        if self.infos['state']['status'] == 'started':
            self.client.bots.make_move(game_id, move)

    def handle_chat_line(self, chat_line):
        pass


print("Ready to play!")
for event in client.bots.stream_incoming_events():
    if event['type'] == 'challenge':
        challenge = event['challenge']
        if challenge['speed'] in ('bullet', 'blitz', 'rapid', 'classic'):
            if challenge['variant']['short'] in ("Std", "FEN"):
                client.bots.accept_challenge(challenge['id'])
                print('challenge accepted!')
        else:
            client.bots.decline_challenge(challenge['id'])

    elif event['type'] == 'gameStart':
        print("new game")
        game_id = event['game']['id']
        game = Game(client=client, game_id=game_id)
        game.run()

    else:  # challengeDeclined, gameFinish, challengeCanceled
        if event['type'] not in ('challengeDeclined', 'gameFinish', 'challengeCanceled'):
            print('NEW EVENT', event)
