"""API tests: auth, validation, CRUD, pagination, filters, summaries, receipts."""
from datetime import date, timedelta

import pytest

from tests.conftest import make_user

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def add(client, headers, **overrides):
    body = {"title": "Lunch", "amount": 120.0, "category": "food", "date": "2026-06-02"}
    body.update(overrides)
    return client.post("/expenses/", json=body, headers=headers)


# ── Auth ────────────────────────────────────────────────
def test_register_validation_and_duplicates(client):
    ok = client.post("/users/register", json={
        "username": "dup_user", "email": "dup@example.com", "password": "password123"})
    assert ok.status_code == 201

    same_name = client.post("/users/register", json={
        "username": "dup_user", "email": "other@example.com", "password": "password123"})
    assert same_name.status_code == 400

    same_email = client.post("/users/register", json={
        "username": "dup_user2", "email": "DUP@example.com", "password": "password123"})
    assert same_email.status_code == 400          # used to crash with 500

    for bad in ({"username": "a", "email": "x@y.com", "password": "password123"},
                {"username": "valid_name", "email": "nope", "password": "password123"},
                {"username": "valid_name", "email": "x@y.com", "password": "short"}):
        assert client.post("/users/register", json=bad).status_code == 422


def test_login_and_token_required(client):
    make_user(client, "login_user")
    bad = client.post("/users/login", data={"username": "login_user", "password": "wrong-pass"})
    assert bad.status_code == 401
    assert client.get("/expenses/").status_code == 401
    assert client.get("/expenses/", headers={"Authorization": "Bearer junk"}).status_code == 401


# ── Create + validation ─────────────────────────────────
def test_create_rounds_amount(client, headers):
    res = add(client, headers, amount=250.555)
    assert res.status_code == 201
    assert res.json()["amount"] == 250.56
    assert res.json()["category"] == "food"


@pytest.mark.parametrize("overrides", [
    {"amount": -1},
    {"amount": 0},
    {"title": "   "},
    {"date": str(date.today() + timedelta(days=1))},
    {"category": "xyz"},            # used to crash with 500 and corrupt the list
])
def test_create_rejects_invalid_input(client, headers, overrides):
    assert add(client, headers, **overrides).status_code == 422


def test_invalid_category_does_not_break_listing(client, headers):
    add(client, headers)
    add(client, headers, category="xyz")
    res = client.get("/expenses/", headers=headers)
    assert res.status_code == 200 and res.json()["total"] == 1


# ── Update ──────────────────────────────────────────────
def test_put_and_patch_apply_same_rules(client, headers):
    exp_id = add(client, headers).json()["id"]

    assert client.patch(f"/expenses/{exp_id}", json={"amount": -5}, headers=headers).status_code == 422
    assert client.patch(f"/expenses/{exp_id}", json={"title": None}, headers=headers).status_code == 422
    assert client.patch(f"/expenses/{exp_id}", json={"category": "xyz"}, headers=headers).status_code == 422
    future = str(date.today() + timedelta(days=3))
    assert client.patch(f"/expenses/{exp_id}", json={"date": future}, headers=headers).status_code == 422

    ok = client.patch(f"/expenses/{exp_id}", json={"amount": 99.999, "category": "health"}, headers=headers)
    assert ok.status_code == 200
    assert ok.json()["amount"] == 100.0 and ok.json()["category"] == "health"
    assert ok.json()["title"] == "Lunch"          # untouched fields stay the same

    put = client.put(f"/expenses/{exp_id}", headers=headers, json={
        "title": "Taxi", "amount": 300, "category": "transport", "date": "2026-05-01"})
    assert put.status_code == 200 and put.json()["title"] == "Taxi"
    assert client.put(f"/expenses/{exp_id}", headers=headers, json={
        "title": "Taxi", "amount": -3, "category": "transport", "date": "2026-05-01"}).status_code == 422


# ── Pagination + filters ────────────────────────────────
def test_pagination(client, headers):
    for day in range(1, 6):
        add(client, headers, title=f"E{day}", date=f"2026-03-0{day}")

    page1 = client.get("/expenses/?page=1&limit=2", headers=headers).json()
    page3 = client.get("/expenses/?page=3&limit=2", headers=headers).json()
    assert page1["total"] == 5 and len(page1["data"]) == 2
    assert [e["title"] for e in page1["data"]] == ["E5", "E4"]   # newest first
    assert len(page3["data"]) == 1

    for bad in ("page=0", "limit=0", "limit=-1", "limit=101"):
        assert client.get(f"/expenses/?{bad}", headers=headers).status_code == 422


def test_filter(client, headers):
    add(client, headers, category="food", date="2026-01-10")
    add(client, headers, category="transport", date="2026-02-10")
    food = client.get("/expenses/filter?category=food", headers=headers).json()
    assert len(food) == 1 and food[0]["category"] == "food"
    ranged = client.get("/expenses/filter?from_date=2026-02-01&to_date=2026-02-28", headers=headers).json()
    assert len(ranged) == 1
    assert client.get("/expenses/filter?category=xyz", headers=headers).status_code == 422
    assert client.get("/expenses/filter?from_date=2026-03-01&to_date=2026-01-01",
                      headers=headers).status_code == 400


# ── Summaries ───────────────────────────────────────────
def test_monthly_report(client, headers):
    add(client, headers, amount=100, date="2026-01-05")
    add(client, headers, amount=250.555, date="2026-06-02")
    add(client, headers, amount=50, date="2026-06-20")
    add(client, headers, amount=999, date="2025-06-20")   # other year — excluded

    report = client.get("/summary/monthly?year=2026", headers=headers).json()
    assert report == {
        "year": 2026,
        "monthly_breakdown": {"January": 100.0, "June": 300.56},
        "highest_spending_month": "June",
        "total_for_year": 400.56,
    }

    empty = client.get("/summary/monthly?year=2020", headers=headers).json()
    assert empty["highest_spending_month"] is None and empty["total_for_year"] == 0.0
    assert client.get("/summary/monthly", headers=headers).status_code == 422
    assert client.get("/summary/monthly?year=99999", headers=headers).status_code == 422


def test_category_total_and_recent(client, headers):
    add(client, headers, category="food", amount=10)
    add(client, headers, category="food", amount=5.5)
    add(client, headers, category="health", amount=20)
    assert client.get("/summary/by-category", headers=headers).json() == {"food": 15.5, "health": 20.0}
    assert client.get("/summary/total", headers=headers).json() == {"total_spent": 35.5}
    assert len(client.get("/summary/recent", headers=headers).json()) == 3


# ── Isolation + delete ──────────────────────────────────
def test_users_only_see_their_own_expenses(client, headers):
    exp_id = add(client, headers).json()["id"]
    other = make_user(client, "isolation_other")
    assert client.get(f"/expenses/{exp_id}", headers=other).status_code == 404
    assert client.delete(f"/expenses/{exp_id}", headers=other).status_code == 404
    assert client.get("/expenses/", headers=other).json()["total"] == 0


def test_delete(client, headers):
    exp_id = add(client, headers).json()["id"]
    assert client.delete(f"/expenses/{exp_id}", headers=headers).status_code == 204
    assert client.get(f"/expenses/{exp_id}", headers=headers).status_code == 404


# ── Receipts ────────────────────────────────────────────
def test_receipt_upload_checks_real_file_type(client, headers):
    import os
    exp_id = add(client, headers).json()["id"]

    fake = client.post(f"/expenses/{exp_id}/receipt", headers=headers,
                       files={"file": ("evil.exe", b"MZ not an image", "image/png")})
    assert fake.status_code == 400

    wrong_type = client.post(f"/expenses/{exp_id}/receipt", headers=headers,
                             files={"file": ("doc.pdf", b"%PDF", "application/pdf")})
    assert wrong_type.status_code == 400

    big = client.post(f"/expenses/{exp_id}/receipt", headers=headers,
                      files={"file": ("big.png", PNG + b"0" * (5 * 1024 * 1024), "image/png")})
    assert big.status_code == 400

    first = client.post(f"/expenses/{exp_id}/receipt", headers=headers,
                        files={"file": ("photo.weird-ext", PNG, "image/png")})
    assert first.status_code == 200 and first.json()["saved_as"].endswith(".png")
    first_path = client.get(f"/expenses/{exp_id}", headers=headers).json()["receipt_path"]
    assert os.path.isfile(first_path)

    second = client.post(f"/expenses/{exp_id}/receipt", headers=headers,
                         files={"file": ("photo.jpg", JPG, "image/jpeg")})
    assert second.status_code == 200
    second_path = client.get(f"/expenses/{exp_id}", headers=headers).json()["receipt_path"]
    assert not os.path.exists(first_path)         # old receipt replaced, not orphaned

    client.delete(f"/expenses/{exp_id}", headers=headers)
    assert not os.path.exists(second_path)        # deleting the expense removes its receipt
