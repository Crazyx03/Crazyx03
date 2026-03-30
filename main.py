import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def resolve_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        if env_url.startswith("postgres://"):
            return env_url.replace("postgres://", "postgresql+psycopg://", 1)
        if env_url.startswith("postgresql://"):
            return env_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return env_url

    db_path = Path("/tmp/items.db") if os.getenv("VERCEL") else Path("items.db")
    return f"sqlite:///{db_path}"


DATABASE_URL = resolve_database_url()
engine: Engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

app = FastAPI(title="Example Items API", version="3.0.0")


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)


class Item(ItemCreate):
    id: int


def init_db() -> None:
    create_sql = (
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL CHECK(price > 0)
        )
        """
        if IS_SQLITE
        else
        """
        CREATE TABLE IF NOT EXISTS items (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            price DOUBLE PRECISION NOT NULL CHECK(price > 0)
        )
        """
    )
    with engine.begin() as conn:
        conn.execute(text(create_sql))


def reset_db() -> None:
    init_db()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM items"))


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
        "database_url": DATABASE_URL.split("@")[-1],
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
    with engine.begin() as conn:
        if IS_SQLITE:
            conn.execute(
                text("INSERT INTO items(name, price) VALUES (:name, :price)"),
                {"name": payload.name, "price": payload.price},
            )
            item_id = conn.execute(text("SELECT last_insert_rowid()")).scalar_one()
        else:
            item_id = conn.execute(
                text("INSERT INTO items(name, price) VALUES (:name, :price) RETURNING id"),
                {"name": payload.name, "price": payload.price},
            ).scalar_one()

        row = conn.execute(
            text("SELECT id, name, price FROM items WHERE id = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    init_db()
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT id, name, price FROM items WHERE id = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    init_db()
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT id, name, price FROM items ORDER BY id")).mappings().all()
    return [Item(id=row["id"], name=row["name"], price=row["price"]) for row in rows]


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemCreate) -> Item:
    init_db()
    with engine.begin() as conn:
        updated = conn.execute(
            text("UPDATE items SET name = :name, price = :price WHERE id = :item_id"),
            {"name": payload.name, "price": payload.price, "item_id": item_id},
        )
        if updated.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        row = conn.execute(
            text("SELECT id, name, price FROM items WHERE id = :item_id"),
            {"item_id": item_id},
        ).mappings().first()
    return Item(id=row["id"], name=row["name"], price=row["price"])


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    init_db()
    with engine.begin() as conn:
        deleted = conn.execute(
            text("DELETE FROM items WHERE id = :item_id"),
            {"item_id": item_id},
        )
    if deleted.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
