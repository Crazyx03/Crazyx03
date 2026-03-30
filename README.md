# Example Items API

A minimal FastAPI example with in-memory CRUD endpoints.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

## Test

```bash
pytest -q
```

## Endpoints

- `GET /health`
- `POST /items`
- `GET /items`
- `GET /items/{item_id}`
- `PUT /items/{item_id}`
- `DELETE /items/{item_id}`

## Validation rules

- `name` must be between 1 and 100 characters.
- `price` must be greater than `0`.

Interactive docs are available at `http://127.0.0.1:8000/docs`.
