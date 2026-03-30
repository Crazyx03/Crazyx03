import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


def resolve_db_path() -> Path:
    env_path = os.getenv("ITEMS_DB_PATH")
    if env_path:
        return Path(env_path)
    if os.getenv("VERCEL"):
        return Path("/tmp/items.db")
    return Path("items.db")


DB_PATH = resolve_db_path()

app = FastAPI(title="Example Items API", version="2.1.0")


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)


class Item(ItemCreate):
    id: int


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK(price > 0)
            )
            """
        )


def reset_db() -> None:
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'items'")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Items API is running",
        "health": "/health",
        "docs": "/docs",
        "app": "/app",
        "db_path": str(DB_PATH),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/app", response_class=HTMLResponse)
def app_ui() -> str:
    return Path("templates/app.html").read_text(encoding="utf-8")

@app.post("/items", response_model=Item, status_code=201)
def create_item(payload: ItemCreate) -> Item:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO items(name, price) VALUES (?, ?)",
            (payload.name, payload.price),
        )
        item_id = cursor.lastrowid
        row = conn.execute("SELECT id, name, price FROM items WHERE id = ?", (item_id,)).fetchone()
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT id, name, price FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, price FROM items ORDER BY id").fetchall()
    return [Item(id=row["id"], name=row["name"], price=row["price"]) for row in rows]


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemCreate) -> Item:
    init_db()
    with get_connection() as conn:
        updated = conn.execute(
            "UPDATE items SET name = ?, price = ? WHERE id = ?",
            (payload.name, payload.price, item_id),
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        row = conn.execute("SELECT id, name, price FROM items WHERE id = ?", (item_id,)).fetchone()
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    init_db()
    with get_connection() as conn:
        deleted = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
