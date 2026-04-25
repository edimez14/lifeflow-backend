from __future__ import annotations


def test_create_public_workspace(client) -> None:
    """Create a public workspace and verify the response shape."""

    payload = {
        "name": "Personal",
        "workspace_type": "public",
        "color": "#3B82F6",
        "icon": "home",
    }

    response = client.post("/workspaces", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Personal"
    assert data["workspace_type"] == "public"
    assert "id" in data
    assert "password_hash" not in data


def test_create_private_workspace(client) -> None:
    """Create a private workspace and ensure password hash is hidden."""

    payload = {
        "name": "Team",
        "workspace_type": "private",
        "password": "super-secret",
        "color": "#10B981",
        "icon": "lock",
    }

    response = client.post("/workspaces", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Team"
    assert data["workspace_type"] == "private"
    assert "password_hash" not in data


def test_list_workspaces(client) -> None:
    """List created workspaces."""

    first_payload = {
        "name": "Workspace A",
        "workspace_type": "public",
        "color": "#111111",
        "icon": "a",
    }
    second_payload = {
        "name": "Workspace B",
        "workspace_type": "public",
        "color": "#222222",
        "icon": "b",
    }

    client.post("/workspaces", json=first_payload)
    client.post("/workspaces", json=second_payload)

    response = client.get("/workspaces")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert "password_hash" not in data[0]


def test_update_workspace_name(client) -> None:
    """Update workspace name using PUT endpoint."""

    payload = {
        "name": "Initial Name",
        "workspace_type": "public",
        "color": "#F97316",
        "icon": "sparkles",
    }
    created = client.post("/workspaces", json=payload).json()

    response = client.put(
        f"/workspaces/{created['id']}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "Updated Name"
    assert "password_hash" not in data


def test_delete_workspace(client) -> None:
    """Delete workspace and verify it no longer exists."""

    payload = {
        "name": "To Delete",
        "workspace_type": "public",
        "color": "#EF4444",
        "icon": "trash",
    }
    created = client.post("/workspaces", json=payload).json()

    delete_response = client.delete(f"/workspaces/{created['id']}")
    get_response = client.get(f"/workspaces/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
