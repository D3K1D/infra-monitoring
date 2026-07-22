from app import models
from app.security import hash_password, verify_password


def register(client, username, password="password123"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )


def login(client, username, password="password123"):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def test_password_hash_round_trip():
    password_hash = hash_password("correct horse battery staple")

    assert password_hash != "correct horse battery staple"
    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_first_account_is_admin_and_later_accounts_are_technicians(client, db):
    first = register(client, "first-admin")
    second = register(client, "second-user")

    assert first.status_code == 201
    assert first.json()["role"] == "admin"
    assert second.status_code == 201
    assert second.json()["role"] == "technician"

    users = db.query(models.User).order_by(models.User.id).all()
    assert verify_password("password123", users[0].password_hash)
    assert users[0].password_hash != "password123"


def test_duplicate_username_and_short_registration_values_are_rejected(client):
    assert register(client, "operator").status_code == 201
    assert register(client, "operator").status_code == 409

    short_username = register(client, "ab")
    short_password = register(client, "another-user", "short")
    assert short_username.status_code == 422
    assert short_password.status_code == 422


def test_login_session_me_and_logout(client):
    register(client, "operator")

    bad_login = login(client, "operator", "not-the-password")
    assert bad_login.status_code == 401

    good_login = login(client, "operator")
    assert good_login.status_code == 200
    cookie_header = good_login.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "operator"

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_only_admins_can_update_thresholds(client):
    register(client, "admin-user")
    register(client, "tech-user")

    login(client, "tech-user")
    forbidden = client.put(
        "/api/thresholds/cpu",
        json={"warning_value": 70, "critical_value": 90},
    )
    assert forbidden.status_code == 403

    login(client, "admin-user")
    updated = client.put(
        "/api/thresholds/cpu",
        json={"warning_value": 70, "critical_value": 90},
    )
    assert updated.status_code == 200
    assert updated.json()["warning_value"] == 70
