import pytest
from app import create_app, db
from app.models import User, Note


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["JWT_SECRET_KEY"] = "test-secret"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def signup(client, username="testuser", email="test@test.com", password="pass"):
    return client.post("/auth/signup", json={
        "username": username, "email": email, "password": password
    })


def login(client, username="testuser", password="pass"):
    return client.post("/auth/login", json={
        "username": username, "password": password
    })


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ─────────────────────────────────────────────────────────────────

def test_signup_success(client):
    res = signup(client)
    assert res.status_code == 201
    assert "access_token" in res.get_json()

def test_signup_duplicate_username(client):
    signup(client)
    res = signup(client)
    assert res.status_code == 422

def test_signup_missing_fields(client):
    res = client.post("/auth/signup", json={"username": "only"})
    assert res.status_code == 422

def test_login_success(client):
    signup(client)
    res = login(client)
    assert res.status_code == 200
    assert "access_token" in res.get_json()

def test_login_wrong_password(client):
    signup(client)
    res = login(client, password="wrongpass")
    assert res.status_code == 401

def test_login_unknown_user(client):
    res = login(client, username="ghost")
    assert res.status_code == 401

def test_me_authenticated(client):
    signup(client)
    token = login(client).get_json()["access_token"]
    res = client.get("/auth/me", headers=auth_header(token))
    assert res.status_code == 200
    assert res.get_json()["username"] == "testuser"

def test_me_unauthenticated(client):
    res = client.get("/auth/me")
    assert res.status_code == 401

# ── Notes Tests ────────────────────────────────────────────────────────────────

def test_create_note(client):
    signup(client)
    token = login(client).get_json()["access_token"]
    res = client.post("/notes/", json={"title": "Test", "content": "Hello"},
                      headers=auth_header(token))
    assert res.status_code == 201
    assert res.get_json()["title"] == "Test"

def test_get_notes_paginated(client):
    signup(client)
    token = login(client).get_json()["access_token"]
    headers = auth_header(token)
    for i in range(7):
        client.post("/notes/", json={"title": f"Note {i}", "content": "..."}, headers=headers)
    res = client.get("/notes/?page=1&per_page=5", headers=headers)
    data = res.get_json()
    assert res.status_code == 200
    assert len(data["notes"]) == 5
    assert data["total"] == 7

def test_get_single_note(client):
    signup(client)
    token = login(client).get_json()["access_token"]
    headers = auth_header(token)
    note_id = client.post("/notes/", json={"title": "T", "content": "C"},
                          headers=headers).get_json()["id"]
    res = client.get(f"/notes/{note_id}", headers=headers)
    assert res.status_code == 200

def test_update_note(client):
    signup(client)
    token = login(client).get_json()["access_token"]
    headers = auth_header(token)
    note_id = client.post("/notes/", json={"title": "Old", "content": "C"},
                          headers=headers).get_json()["id"]
    res = client.patch(f"/notes/{note_id}", json={"title": "New"}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["title"] == "New"

def test_delete_note(client):
    signup(client)
    token = login(client).get_json()["access_token"]
    headers = auth_header(token)
    note_id = client.post("/notes/", json={"title": "Del", "content": "C"},
                          headers=headers).get_json()["id"]
    res = client.delete(f"/notes/{note_id}", headers=headers)
    assert res.status_code == 200

def test_cannot_access_other_users_note(client):
    # User A creates a note
    signup(client, username="userA", email="a@a.com")
    token_a = login(client, username="userA").get_json()["access_token"]
    note_id = client.post("/notes/", json={"title": "Private", "content": "secret"},
                          headers=auth_header(token_a)).get_json()["id"]

    # User B tries to access it
    signup(client, username="userB", email="b@b.com")
    token_b = login(client, username="userB").get_json()["access_token"]
    res = client.get(f"/notes/{note_id}", headers=auth_header(token_b))
    assert res.status_code == 403

def test_cannot_delete_other_users_note(client):
    signup(client, username="userA", email="a@a.com")
    token_a = login(client, username="userA").get_json()["access_token"]
    note_id = client.post("/notes/", json={"title": "Private", "content": "secret"},
                          headers=auth_header(token_a)).get_json()["id"]

    signup(client, username="userB", email="b@b.com")
    token_b = login(client, username="userB").get_json()["access_token"]
    res = client.delete(f"/notes/{note_id}", headers=auth_header(token_b))
    assert res.status_code == 403

def test_notes_require_auth(client):
    res = client.get("/notes/")
    assert res.status_code == 401