import berserk
import time

import skormfish as sk

API_TOKEN = open("api_token.txt").read()
bot_id = 'skormfish'

session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)


class Game:
    def __init__(self, client, game_id, bot=sk.Skormfish(time_limit=5), **kwargs):
        super().__init__(**kwargs)
        self.game_id = game_id
        self.client = client
        self.stream = client.bots.stream_game_state(game_id)
        self.infos = next(self.stream)
        self.bot_white = self.infos['white'].get('id') == bot_id
        self.current_state = self.infos['state']
        self.ctime = "wtime" if self.bot_white else "btime"
        self.bot = bot
        self.moves = ""

    def run(self):
        print('game start!')
        client.bots.post_message(game_id, 'Good luck\nHave fun')

        # From Position
        if self.infos['variant']['short'] == "FEN":
            self.bot.from_pos(self.infos['initialFen'])
            if self.bot_white:
                self.make_first_move()

        # Reconnect to a game
        elif self.moves != self.current_state['moves']:
            self.bot.from_moves(self.current_state['moves'])
            self.handle_state_change(self.current_state)

        # You start
        elif self.bot_white and self.moves == "":
            self.make_first_move()

        # Game loop
        for event in self.stream:
            if event['type'] == 'gameState':
                if event['status'] == 'started':
                    self.handle_state_change(event)
                elif event['status'] in ('mate', 'resign', 'outoftime', 'aborted'):
                    client.bots.post_message(game_id, 'Good game\nWell played')
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

        if bot_turn:
            # time management
            remaining = game_state[self.ctime]
            time_limit = (remaining / 1000 if isinstance(remaining, int) else (
                        remaining.minute * 60 + remaining.second)) / 40
            time_limit = min(self.bot.time_limit, time_limit)
            depth = move = score = None
            start = time.time()

            # Look for a move
            for depth, move, score in self.bot.search(pos):
                # print(f"depth: {depth} - time: {round(time.time() - start, 2)} seconds")
                if time.time() - start > time_limit:
                    break
            actual_time = time.time() - start

            # Play the move
            move = sk.mrender(pos, move)
            self.client.bots.make_move(game_id, move)

            print("-" * 40)
            print(f"depth: {depth} - time: {round(actual_time, 2)} seconds")
            print(f"score: {score} - time delta: {round(actual_time - time_limit, 2)}")

    def make_first_move(self):
        pos = self.bot.hist[-1]
        start = time.time()
        depth = move = score = None
        for depth, move, score in self.bot.search(pos):
            if time.time() - start > self.bot.time_limit:
                break
        # Play the move
        move = sk.mrender(pos, move)
        self.client.bots.make_move(game_id, move)

    def handle_chat_line(self, chat_line):
        pass


for event in client.bots.stream_incoming_events():

    if event['type'] == 'challenge':
        challenge = event['challenge']
        if challenge['speed'] in ('bullet', 'blitz', 'rapid', 'classic'):
            if challenge['variant']['short'] in ("Std", "FEN"):
                client.bots.accept_challenge(challenge['id'])
        else:
            client.bots.decline_challenge(challenge['id'])
        print('challenge accepted!')

    elif event['type'] == 'gameStart':
        game_id = event['game']['id']
        game = Game(client=client, game_id=game_id)
        game.run()

    else:  # challengeDeclined, gameFinish, challengeCanceled
        if event['type'] not in ('challengeDeclined', 'gameFinish', 'challengeCanceled'):
            print('NEW EVENT', event)
