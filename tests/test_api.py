from fastapi.testclient import TestClient

from main import app, init_db, reset_db

client = TestClient(app)


def setup_function() -> None:
    init_db()
    reset_db()


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/health"


def test_app_ui() -> None:
    response = client.get("/app")
    assert response.status_code == 200
    assert "Items App" in response.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_item() -> None:
    create = client.post("/items", json={"name": "Widget", "price": 9.99})
    assert create.status_code == 201
    created = create.json()
    assert created["id"] == 1

    fetched = client.get("/items/1")
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_list_items() -> None:
    client.post("/items", json={"name": "One", "price": 1.0})
    client.post("/items", json={"name": "Two", "price": 2.0})

    response = client.get("/items")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["name"] == "One"
    assert body[1]["name"] == "Two"


def test_update_item() -> None:
    client.post("/items", json={"name": "Before", "price": 5.0})

    response = client.put("/items/1", json={"name": "After", "price": 7.5})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "After", "price": 7.5}


def test_delete_item() -> None:
    client.post("/items", json={"name": "Delete", "price": 3.0})

    deleted = client.delete("/items/1")
    assert deleted.status_code == 204

    missing = client.get("/items/1")
    assert missing.status_code == 404


def test_not_found_paths() -> None:
    assert client.get("/items/999").status_code == 404
    assert client.put("/items/999", json={"name": "X", "price": 1.0}).status_code == 404
    assert client.delete("/items/999").status_code == 404


def test_validation_errors() -> None:
    empty_name = client.post("/items", json={"name": "", "price": 1.0})
    assert empty_name.status_code == 422

    non_positive_price = client.post("/items", json={"name": "X", "price": 0})
    assert non_positive_price.status_code == 422
