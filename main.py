from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route

import sqlite3
import asyncio
import time

DB_PATH = "users.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """
    )

    conn.commit()
    conn.close()

async def hello(request: Request):
    return JSONResponse({
        "message": "hello from hello api",
        "headers": dict(request.headers)
    })

async def ping(request: Request):
    return JSONResponse({
        "status": "ok",
        "ts": time.time()
    })

async def slow(request: Request):
    await asyncio.sleep(2)
    return JSONResponse({
        "message": "this ones does a sleep of 2 seconds"
    })

async def create_user(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")

    if not name or not email:
        return JSONResponse({
            "error": "name and email required"
        }, status = 400)
    
    conn = get_db()
    current = conn.execute(
        "INSERT INTO users(name, email) VALUES (?, ?)", (name, email)
    )
    conn.commit()

    user_id = current.lastrowid
    conn.close()

    return JSONResponse({
        "id": user_id,
        "name": name,
        "email": email
    }, status_code = 201)


async def list_user(request: Request):
    conn = get_db()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return JSONResponse([dict(row) for row in rows])


async def get_user(request: Request):
    user_id = request.path_params["user_id"]
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = (?)", (user_id, )).fetchone()
    conn.close()

    if row is None:
        return JSONResponse({
            "error": "not found"
        }, status_code = 404)
    
    return JSONResponse(dict(row))


async def delete_user(request: Request):
    user_id = request.path_params["user_id"]

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id, ))
    conn.commit()
    conn.close()

    return Response(status_code = 204)


app = Starlette(debug = True, routes = [
    Route("/hello", hello, methods = ["GET"]),
    Route("/ping", ping, methods = ["GET"]),
    Route("/slow", slow, methods = ["GET"]),

    Route("/users", create_user, methods = ["POST"]),
    Route("/users", list_user, methods = ["GET"]),

    Route("/users/{user_id:int}", get_user, methods = ["GET"]),
    Route("/users/{user_id:int}", delete_user, methods = ["DELETE"]),
])


init_db()


