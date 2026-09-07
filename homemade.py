"""
Some example classes for people who want to create a homemade bot.

With these classes, bot makers will not have to implement the UCI or XBoard interfaces themselves.
"""
import chess
from chess.engine import PlayResult, Limit
import random
from lib.engine_wrapper import MinimalEngine
from lib.lichess_types import MOVE, HOMEMADE_ARGS_TYPE
import logging

from copy import deepcopy as copy


# Use this logger variable to print messages to the console or log files.
# logger.info("message") will always print "message" to the console or log file.
# logger.debug("message") will only print "message" if verbose logging is enabled.
logger = logging.getLogger(__name__)


class ExampleEngine(MinimalEngine):
    """An example engine that all homemade engines inherit."""


# Bot names and ideas from tom7's excellent eloWorld video

class RandomMove(ExampleEngine):
    """Get a random move."""

    def search(self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE) -> PlayResult:  # noqa: ARG002
        """Choose a random move."""
        return PlayResult(random.choice(list(board.legal_moves)), None)


class Alphabetical(ExampleEngine):
    """Get the first move when sorted by san representation."""

    def search(self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE) -> PlayResult:  # noqa: ARG002
        """Choose the first move alphabetically."""
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return PlayResult(moves[0], None)


class FirstMove(ExampleEngine):
    """Get the first move when sorted by uci representation."""

    def search(self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE) -> PlayResult:  # noqa: ARG002
        """Choose the first move alphabetically in uci representation."""
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return PlayResult(moves[0], None)


class ComboEngine(ExampleEngine):
    """
    Get a move using multiple different methods.

    This engine demonstrates how one can use `time_limit`, `draw_offered`, and `root_moves`.
    """

    def search(self,
               board: chess.Board,
               time_limit: Limit,
               ponder: bool,  # noqa: ARG002
               draw_offered: bool,
               root_moves: MOVE) -> PlayResult:
        """
        Choose a move using multiple different methods.

        :param board: The current position.
        :param time_limit: Conditions for how long the engine can search (e.g. we have 10 seconds and search up to depth 10).
        :param ponder: Whether the engine can ponder after playing a move.
        :param draw_offered: Whether the bot was offered a draw.
        :param root_moves: If it is a list, the engine should only play a move that is in `root_moves`.
        :return: The move to play.
        """
        if isinstance(time_limit.time, int):
            my_time = time_limit.time
            my_inc = 0
        elif board.turn == chess.WHITE:
            my_time = time_limit.white_clock if isinstance(time_limit.white_clock, int) else 0
            my_inc = time_limit.white_inc if isinstance(time_limit.white_inc, int) else 0
        else:
            my_time = time_limit.black_clock if isinstance(time_limit.black_clock, int) else 0
            my_inc = time_limit.black_inc if isinstance(time_limit.black_inc, int) else 0

        possible_moves = root_moves if isinstance(root_moves, list) else list(board.legal_moves)

        if my_time / 60 + my_inc > 10:
            # Choose a random move.
            move = random.choice(possible_moves)
        else:
            # Choose the first move alphabetically in uci representation.
            possible_moves.sort(key=str)
            move = possible_moves[0]
        return PlayResult(move, None, draw_offered=draw_offered)

class MainEngine(ExampleEngine):
    
    depth = 4
    def search(self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE) -> PlayResult:
        board = board
        my_side = board.turn
        original_move_list = list(board.legal_moves)
        original_moves = {}
        for omove in original_move_list:
            board.push(omove)
            evalu = self.recursive_search(board, 2)
            if evalu in original_moves.keys():
                original_moves[evalu].append(omove)
            else:
                original_moves[evalu] = [omove]
            board.pop()

        return PlayResult(random.choice(original_moves[max(original_moves.keys())]), None)

    def recursive_search(self, board, depth):
        move_list = list(board.legal_moves)
        moves = {}

        score = -99999

        for move in move_list:
            board.push(move)
            if depth > 0:    
                evalu = -self.recursive_search(board, depth-1)
            else:
                evalu = self.eval(board, board.turn)
            
            score = max(score, evalu)

            board.pop()

        return score

    def eval(self, board: chess.Board, my_side: bool) -> int:
        score = 0

        score += len(board.pieces(chess.PAWN, chess.WHITE)) * 1
        score += len(board.pieces(chess.KNIGHT, chess.WHITE)) * 3
        score += len(board.pieces(chess.BISHOP, chess.WHITE)) * 3
        score += len(board.pieces(chess.ROOK, chess.WHITE)) * 5
        score += len(board.pieces(chess.QUEEN, chess.WHITE)) * 9
        
        # Black pieces (subtracted)
        score -= len(board.pieces(chess.PAWN, chess.BLACK)) * 1
        score -= len(board.pieces(chess.KNIGHT, chess.BLACK)) * 3
        score -= len(board.pieces(chess.BISHOP, chess.BLACK)) * 3
        score -= len(board.pieces(chess.ROOK, chess.BLACK)) * 5
        score -= len(board.pieces(chess.QUEEN, chess.BLACK)) * 9

        if board.is_checkmate():
            score -= 10000
        elif board.is_stalemate() or board.is_fivefold_repetition() or board.is_insufficient_material():
            score = 0

        if my_side:
            return score
        return -score
