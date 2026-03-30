from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Example Items API", version="1.1.0")


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)


class Item(ItemCreate):
    id: int


# In-memory store for demo purposes.
db: Dict[int, Item] = {}
next_id = 1


def reset_store() -> None:
    """Reset in-memory state. Used by tests."""
    global next_id
    db.clear()
    next_id = 1


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", response_model=Item, status_code=201)
def create_item(payload: ItemCreate) -> Item:
    global next_id
    item = Item(id=next_id, **payload.model_dump())
    db[next_id] = item
    next_id += 1
    return item


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    item = db.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return list(db.values())


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemCreate) -> Item:
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    db[item_id] = Item(id=item_id, **payload.model_dump())
    return db[item_id]


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]
