import random

import chess
import chess.svg
from .utils import rand_id
from .chess_ai import get_ai_move

class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.id = rand_id()
        self.__player = random.choice(chess.COLORS)
        self.waiting = False
        self.__finished_ai_turn = False
    
    def run_ai_turn(self):
        if self.waiting or self.is_player_turn():
            return
        self.waiting = True
        try:
            move = get_ai_move(self.board)
            self.board.push(move)
            self.__finished_ai_turn = True
            
        except:
            self.waiting = False

    def finished_ai_turn(self):
        if self.__finished_ai_turn:
            self.__finished_ai_turn = False
            return True
        return False

    def is_player_turn(self):
        return self.board.turn == self.__player

    def get_board_as_svg(self):
        svg = chess.svg.board(self.board, orientation=self.__player)
        return svg

    @property
    def is_over(self):
        return self.board.is_game_over()

    def get_result(self):
        winner = self.board.outcome().winner
        if winner is None:
            return "draw"
        return chess.COLOR_NAMES[winner]