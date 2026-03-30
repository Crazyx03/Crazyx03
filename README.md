# Example Items API

A FastAPI example with CRUD endpoints and SQLite-backed persistence.

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

## Persistence

- Data is stored in a local SQLite database file: `items.db`.
- Tests automatically clear the table and remove the DB file after execution.

Interactive docs are available at `http://127.0.0.1:8000/docs`.


## Deploy on Vercel

- The project includes `api/index.py` so Vercel can expose the ASGI app as a Python Function.
- `vercel.json` rewrites all incoming paths to `/api` so routes like `/health`, `/items`, and `/docs` resolve correctly.
- Optional: set the project Root Directory correctly in Vercel if using a monorepo.
