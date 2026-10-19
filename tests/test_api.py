def post_expense(client, **overrides):
    payload = {
        "amount": 2500,
        "category": "transport",
        "description": "Такси",
        "spent_on": "2026-10-10",
    }
    payload.update(overrides)
    return client.post("/api/expenses", json=payload)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["environment"] == "test"


def test_index_page(client):
    post_expense(client)
    response = client.get("/")
    assert response.status_code == 200
    assert "ExpenseTracker" in response.get_data(as_text=True)
    assert "Такси" in response.get_data(as_text=True)


def test_categories(client):
    assert "food" in client.get("/api/categories").json


def test_create_and_get_expense(client):
    created = post_expense(client)
    assert created.status_code == 201
    expense_id = created.json["id"]
    fetched = client.get(f"/api/expenses/{expense_id}")
    assert fetched.status_code == 200
    assert fetched.json["amount"] == 2500.0


def test_create_invalid_expense(client):
    response = post_expense(client, amount=-1)
    assert response.status_code == 400
    assert "error" in response.json


def test_create_without_json(client):
    assert client.post("/api/expenses", data="oops").status_code == 400


def test_list_with_filters(client):
    post_expense(client, category="food", spent_on="2026-10-01")
    post_expense(client, category="transport", spent_on="2026-09-01")
    assert len(client.get("/api/expenses").json) == 2
    assert len(client.get("/api/expenses?category=food").json) == 1
    assert len(client.get("/api/expenses?month=2026-09").json) == 1
    assert client.get("/api/expenses?category=unknown").status_code == 400


def test_delete_expense(client):
    expense_id = post_expense(client).json["id"]
    assert client.delete(f"/api/expenses/{expense_id}").status_code == 204
    assert client.get(f"/api/expenses/{expense_id}").status_code == 404
    assert client.delete(f"/api/expenses/{expense_id}").status_code == 404


def test_summary(client):
    post_expense(client, amount=1000, category="food")
    post_expense(client, amount=250.5, category="food")
    post_expense(client, amount=3000, category="housing")
    summary = client.get("/api/summary").json
    assert summary["count"] == 3
    assert summary["total"] == 4250.5
    assert summary["by_category"]["food"] == 1250.5


def test_summary_categories_sorted_by_amount(client):
    post_expense(client, amount=100, category="food")
    post_expense(client, amount=900, category="transport")
    post_expense(client, amount=500, category="health")
    summary = client.get("/api/summary").json
    assert list(summary["by_category"]) == ["transport", "health", "food"]


def test_form_add_and_delete(client, store):
    response = client.post(
        "/expenses/add",
        data={
            "amount": "700",
            "category": "health",
            "description": "Аптека",
            "spent_on": "2026-10-03",
        },
    )
    assert response.status_code == 302
    expense = store.list()[0]
    assert expense.description == "Аптека"
    client.post(f"/expenses/{expense.id}/delete")
    assert store.list() == []


def test_form_validation_error_redirects_with_message(client):
    response = client.post("/expenses/add", data={"amount": "0", "category": "food"})
    assert response.status_code == 302
    assert "error=" in response.headers["Location"]
