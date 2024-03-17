import os
from contextlib import asynccontextmanager
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Body, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from .chess import ChessGame
from .jinja import render_template, render_macro

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.games = {}
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY"))


def has_game(game_id: str) -> bool:
    return game_id in app.state.games


def get_game(game_id: str) -> ChessGame:
    return app.state.games[game_id]


def create_game() -> ChessGame:
    game = ChessGame()
    app.state.games[game.id] = game
    return game


def game_session(request: Request):
    game_id = request.session.get("game_id", None)
    if game_id is None or not has_game(game_id):
        raise HTTPException(status_code=404, detail="Invalid game_id")
    return get_game(game_id)


@app.get("/newgame")
def new_game(request: Request):
    if (game_id := request.session.get("game_id", None)) and has_game(game_id):
        del app.state.games[game_id]
    game = create_game()
    request.session["game_id"] = game.id
    return JSONResponse(
        {"game_id": game.id, "board": game.board.fen()}, headers={"HX-Refresh": "true"}
    )


@app.get("/board/fen")
def get_board(game: Annotated[ChessGame, Depends(game_session)]):
    return {"board": game.board.fen()}


@app.get("/status")
def get_status(
    game: Annotated[ChessGame, Depends(game_session)], tasks: BackgroundTasks
):
    if game.is_over:
        return {"status": "finished", "result": game.get_result()}

    if game.is_player_turn():
        return {"status": "player_turn"}

    if not game.waiting:
        tasks.add_task(game.run_ai_turn)
    return {"status": "ai_turn"}


@app.post("/move/san")
def move(
    game: Annotated[ChessGame, Depends(game_session)],
    move: Annotated[str, Body(embed=True)],
):
    try:
        game.board.push_san(move)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid move")
    return JSONResponse(
        {"board": game.board.fen()},
        headers={"HX-Trigger": "refreshBoard, refreshAction"},
    )


@app.get("/")
def index(request: Request):
    game_id = request.session.get("game_id", None)
    if game_id is None or not has_game(game_id):
        game = create_game()
        request.session["game_id"] = game_id = game.id
    return HTMLResponse(render_template("index.html", game_id=game_id))


@app.get("/render/board")
def render_board(game: Annotated[ChessGame, Depends(game_session)]):
    return HTMLResponse(game.get_board_as_svg())


@app.get("/render/action")
def render_action(
    game: Annotated[ChessGame, Depends(game_session)], tasks: BackgroundTasks
):
    refreshBoard = {"HX-Trigger": "refreshBoard"}
    if game.is_over:
        return HTMLResponse(render_macro("chess.html:gameOver", game.get_result()), headers=refreshBoard)

    if not game.is_player_turn():
        if not game.waiting:
            tasks.add_task(game.run_ai_turn)
        return HTMLResponse(
            render_macro("chess.html:waiting"), headers={"HX-Trigger": "waitingForTurn"}
        )

    headers = {}
    if game.finished_ai_turn():
        headers |= refreshBoard
    moves = [game.board.san(move) for move in game.board.legal_moves]
    return HTMLResponse(render_macro("chess.html:moves", moves), headers=headers)
