"""Test setup: a temporary SQLite DB and uploads folder for each test session."""
import os
import shutil
import sys
import tempfile

import pytest

TMP_DIR = tempfile.mkdtemp(prefix="expense-tests-")
os.environ.update({
    "SECRET_KEY":   "test-secret-key-that-is-long-enough-123456",
    "DATABASE_URL": f"sqlite:///{os.path.join(TMP_DIR, 'test.db')}",
    "UPLOAD_DIR":   os.path.join(TMP_DIR, "uploads"),
})
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        yield c
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def make_user(client, username):
    client.post("/users/register", json={
        "username": username, "email": f"{username}@example.com", "password": "password123"})
    res = client.post("/users/login", data={"username": username, "password": "password123"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture()
def headers(client, request):
    """A fresh user per test, so each test starts with no expenses"""
    return make_user(client, f"user_{request.node.name[:20].strip('_')}_{id(request) % 10000}")
