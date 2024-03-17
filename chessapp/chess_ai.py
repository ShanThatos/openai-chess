import re

from dotenv import load_dotenv
from openai import OpenAI
import chess
import chess.svg
import chess.pgn

load_dotenv()
client = OpenAI()

TEAM_PROMPTS = [["black", "lowercase"], ["white", "uppercase"]]


def system_prompt(board: chess.Board):
    color = chess.COLOR_NAMES[board.turn]
    return f"""You are playing chess for the {color} team. 
Show your reasoning for every legal move before deciding on a single one. 
End your response with a new line of the form: "**Move: <move>**", where <move> \
is a move in Short Standard Algebraic Notation and contains no unnecessary characters. 
When castling, use the character "O" (uppercase) instead of the number "0"."""


def describe_board(board: chess.Board):
    description = ""
    for color in chess.COLORS:
        for piece in chess.PIECE_TYPES:
            squares = board.pieces(piece, color)
            if not squares:
                continue
            squares_str = " ".join(chess.square_name(square) for square in squares)
            description += f"{chess.COLOR_NAMES[color]} {chess.PIECE_NAMES[piece]}(s): {squares_str}\n"
    return description


def main_prompt(board: chess.Board):
    return f"""Here is the board as a grid:
{str(board)}
The uppercase letters represent the white pieces, and the lowercase letters \
represent the black pieces.
The dots/periods represent empty squares. The pieces are represented by their first letter.
Here is the PGN of the game so far:
{chess.pgn.Game.from_board(board).accept(chess.pgn.StringExporter(columns=None, headers=False, comments=False, variations=False))}
What is your move in Short Standard Algebraic Notation? """


def get_ai_move(board: chess.Board):
    print(f"Turn: {chess.COLOR_NAMES[board.turn]}")
    print(board)
    legal_moves = [board.san(m) for m in board.legal_moves]
    legal_moves_str = ", ".join(legal_moves)
    print(legal_moves_str)

    def find_matching_move(response: str):
        last_line = response.splitlines()[-1]
        match = re.match(r"\*\*Move:([\s\.|\d\.]*)([^\*]*)\*\*", last_line)
        if match is None:
            return None
        move_str = match.group(2)
        return move_str

    messages = [
        {
            "role": "system",
            "content": system_prompt(board),
        },
        {
            "role": "user",
            "content": main_prompt(board),
        },
    ]

    def ask_ai():
        return (
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=3000,
            )
            .choices[0]
            .message.content.strip()
        )

    NUM_ATTEMPTS = 30
    for _ in range(NUM_ATTEMPTS):
        response = ask_ai()
        print(response)
        move_str = find_matching_move(response)
        if move_str not in legal_moves:
            print("Invalid move:", move_str)
            messages.append({"role": "assistant", "content": response})
            if move_str is None:
                messages.append(
                    {
                        "role": "user",
                        "content": f"I could not parse a move from your response. \nEnd your response with one of these legal moves: {legal_moves_str} \nFollow the format specified: **Move: <move>**\n{main_prompt(board)}",
                    }
                )
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": f"{move_str} was not valid. \nMake sure your move is in Short Algebraic Notation. \nHere are the possible moves: {legal_moves_str}\n{main_prompt(board)}",
                    }
                )
        else:
            return board.parse_san(move_str)
    raise Exception(f"AI failed to provide a valid move after {NUM_ATTEMPTS} attempts.")

if __name__ == "__main__":
    board = chess.Board()

    for _ in range(100):
        move = get_ai_move(board)
        board.push(move)
        print("\n\n")

        if board.is_game_over(claim_draw=True):
            print(board.result(claim_draw=True))
            break
