import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path("items.db")

app = FastAPI(title="Example Items API", version="2.0.0")


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)


class Item(ItemCreate):
    id: int


def get_connection() -> sqlite3.Connection:
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
    with get_connection() as conn:
        conn.execute("DELETE FROM items")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'items'")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Items API is running", "health": "/health", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", response_model=Item, status_code=201)
def create_item(payload: ItemCreate) -> Item:
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
    with get_connection() as conn:
        row = conn.execute("SELECT id, name, price FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, price FROM items ORDER BY id").fetchall()
    return [Item(id=row["id"], name=row["name"], price=row["price"]) for row in rows]


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemCreate) -> Item:
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
    with get_connection() as conn:
        deleted = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
