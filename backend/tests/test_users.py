from app import models


def register(client, username):
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()


def login(client, username):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert response.status_code == 200


def test_user_management_is_admin_only(client):
    admin = register(client, "admin-user")
    technician = register(client, "tech-user")

    login(client, "tech-user")
    assert client.get("/api/users").status_code == 403
    assert client.put(
        f"/api/users/{technician['id']}/role",
        json={"role": "admin"},
    ).status_code == 403
    assert client.delete(f"/api/users/{admin['id']}").status_code == 403

    login(client, "admin-user")
    response = client.get("/api/users")
    assert response.status_code == 200
    assert [user["username"] for user in response.json()] == [
        "admin-user",
        "tech-user",
    ]
    assert all(user["created_at"] for user in response.json())


def test_admin_can_promote_and_demote_without_removing_last_admin(client, db):
    admin = register(client, "admin-user")
    technician = register(client, "tech-user")
    login(client, "admin-user")

    last_admin = client.put(
        f"/api/users/{admin['id']}/role",
        json={"role": "technician"},
    )
    assert last_admin.status_code == 400

    promoted = client.put(
        f"/api/users/{technician['id']}/role",
        json={"role": "admin"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"

    invalid = client.put(
        f"/api/users/{technician['id']}/role",
        json={"role": "owner"},
    )
    assert invalid.status_code == 422

    demoted = client.put(
        f"/api/users/{admin['id']}/role",
        json={"role": "technician"},
    )
    assert demoted.status_code == 200
    assert demoted.json()["role"] == "technician"

    db.expire_all()
    assert db.query(models.User).filter(models.User.role == "admin").count() == 1


def test_admin_can_delete_other_users_but_not_self(client, db):
    admin = register(client, "admin-user")
    technician = register(client, "tech-user")
    login(client, "admin-user")

    self_delete = client.delete(f"/api/users/{admin['id']}")
    assert self_delete.status_code == 400

    deleted = client.delete(f"/api/users/{technician['id']}")
    assert deleted.status_code == 204

    db.expire_all()
    assert db.query(models.User).count() == 1
    assert client.delete("/api/users/9999").status_code == 404
