"""Module 2 endpoint tests: POST, GET list, GET one, PATCH (incl. transitions), DELETE."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

RESPONSE_FIELDS = {
    "id", "title", "description", "assignee",
    "status", "priority", "due_date", "tags", "created_at", "updated_at",
    "is_overdue",
}


# ---------------------------------------------------------------- POST /tasks

def test_create_task_valid_returns_201_with_full_body(client: TestClient):
    r = client.post("/tasks", json={"title": "Write tests", "priority": "High"})
    assert r.status_code == 201
    body = r.json()
    assert set(body) == RESPONSE_FIELDS
    assert isinstance(body["id"], int)
    assert body["title"] == "Write tests"
    assert body["description"] == ""
    assert body["assignee"] is None
    assert body["status"] == "ToDo"
    assert body["priority"] == "High"
    assert body["created_at"] == body["updated_at"]


def test_create_task_missing_title_returns_422(client: TestClient):
    r = client.post("/tasks", json={"description": "no title here"})
    assert r.status_code == 422


def test_create_task_blank_title_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "   "})
    assert r.status_code == 422


def test_create_task_invalid_priority_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "x", "priority": "Urgent"})
    assert r.status_code == 422


def test_create_task_unknown_field_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "x", "id": 42})
    assert r.status_code == 422


# ----------------------------------------------------------------- GET /tasks

def test_list_tasks_empty_returns_200_and_empty_list(client: TestClient):
    r = client.get("/tasks")
    assert r.status_code == 200
    assert r.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(
    client: TestClient, created_task: dict
):
    r = client.get("/tasks", params={"status": "Done"})
    assert r.status_code == 200
    assert r.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client: TestClient):
    client.post("/tasks", json={"title": "low", "priority": "Low"})
    client.post("/tasks", json={"title": "high 1", "priority": "High"})
    client.post("/tasks", json={"title": "high 2", "priority": "High"})

    r = client.get("/tasks", params={"priority": "High"})
    assert r.status_code == 200
    body = r.json()
    assert [t["title"] for t in body] == ["high 1", "high 2"]
    assert all(t["priority"] == "High" for t in body)


# ------------------------------------------------------------ GET /tasks/{id}

def test_get_task_by_id_returns_task(client: TestClient, created_task: dict):
    r = client.get(f"/tasks/{created_task['id']}")
    assert r.status_code == 200
    assert r.json() == created_task


def test_get_task_by_id_not_found_returns_404_with_detail(client: TestClient):
    r = client.get("/tasks/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "Task with id 999 not found"}


# ---------------------------------------------------------- PATCH /tasks/{id}

def test_patch_partial_update_keeps_other_fields(client: TestClient):
    created = client.post(
        "/tasks",
        json={"title": "orig", "description": "keep me", "assignee": "sam", "priority": "High"},
    ).json()

    r = client.patch(f"/tasks/{created['id']}", json={"title": "renamed"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "renamed"
    assert body["description"] == "keep me"
    assert body["assignee"] == "sam"
    assert body["priority"] == "High"
    assert body["status"] == "ToDo"
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] >= created["updated_at"]


def test_patch_not_found_returns_404(client: TestClient):
    r = client.patch("/tasks/999", json={"title": "ghost"})
    assert r.status_code == 404
    assert r.json() == {"detail": "Task with id 999 not found"}


def test_patch_valid_transition_todo_to_inprogress_returns_200(
    client: TestClient, created_task: dict
):
    r = client.patch(f"/tasks/{created_task['id']}", json={"status": "InProgress"})
    assert r.status_code == 200
    assert r.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done_returns_422(
    client: TestClient, created_task: dict
):
    r = client.patch(f"/tasks/{created_task['id']}", json={"status": "Done"})
    assert r.status_code == 422
    assert "Invalid status transition from ToDo to Done" in r.json()["detail"]
    # nothing was written
    assert client.get(f"/tasks/{created_task['id']}").json()["status"] == "ToDo"


def test_patch_same_status_returns_422(client: TestClient, created_task: dict):
    r = client.patch(f"/tasks/{created_task['id']}", json={"status": "ToDo"})
    assert r.status_code == 422
    assert "Invalid status transition from ToDo to ToDo" in r.json()["detail"]


def test_patch_with_read_only_field_returns_422(client: TestClient, created_task: dict):
    r = client.patch(
        f"/tasks/{created_task['id']}",
        json={"id": 1, "created_at": created_task["created_at"]},
    )
    assert r.status_code == 422
    rejected = {err["loc"][-1] for err in r.json()["detail"]}
    assert rejected == {"id", "created_at"}
    # nothing was written
    assert client.get(f"/tasks/{created_task['id']}").json() == created_task


# --------------------------------------------------------- DELETE /tasks/{id}

def test_delete_existing_returns_204_no_body(client: TestClient, created_task: dict):
    r = client.delete(f"/tasks/{created_task['id']}")
    assert r.status_code == 204
    assert r.content == b""
    assert client.get(f"/tasks/{created_task['id']}").status_code == 404


def test_delete_missing_returns_404(client: TestClient):
    r = client.delete("/tasks/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "Task with id 999 not found"}


# ------------------------------------------------------------------ Due dates

def test_create_task_with_due_date_returns_201_with_due_date(client: TestClient):
    r = client.post("/tasks", json={"title": "ship it", "due_date": "2030-01-15"})
    assert r.status_code == 201
    body = r.json()
    assert set(body) == RESPONSE_FIELDS
    assert body["due_date"] == "2030-01-15"
    assert body["is_overdue"] is False


@pytest.mark.parametrize("bad_date", ["not-a-date", "2026-13-45"])
def test_create_task_invalid_due_date_returns_422(client: TestClient, bad_date: str):
    r = client.post("/tasks", json={"title": "x", "due_date": bad_date})
    assert r.status_code == 422


def test_create_task_without_due_date_returns_null_due_date(client: TestClient):
    r = client.post("/tasks", json={"title": "someday"})
    assert r.status_code == 201
    body = r.json()
    assert body["due_date"] is None
    assert body["is_overdue"] is False


def test_create_task_past_due_date_returns_is_overdue_true(client: TestClient):
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    r = client.post("/tasks", json={"title": "late", "due_date": yesterday})
    assert r.status_code == 201
    body = r.json()
    assert body["due_date"] == yesterday
    assert body["is_overdue"] is True


def test_patch_past_due_task_to_done_returns_is_overdue_false(client: TestClient):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    created = client.post("/tasks", json={"title": "late", "due_date": yesterday}).json()
    assert created["is_overdue"] is True

    assert client.patch(f"/tasks/{created['id']}", json={"status": "InProgress"}).status_code == 200
    r = client.patch(f"/tasks/{created['id']}", json={"status": "Done"})
    assert r.status_code == 200
    body = r.json()
    assert body["due_date"] == yesterday
    assert body["is_overdue"] is False


def test_patch_due_date_returns_new_due_date(client: TestClient):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    created = client.post("/tasks", json={"title": "late", "due_date": yesterday}).json()

    r = client.patch(f"/tasks/{created['id']}", json={"due_date": "2030-06-01"})
    assert r.status_code == 200
    body = r.json()
    assert body["due_date"] == "2030-06-01"
    assert body["is_overdue"] is False


def test_patch_due_date_null_clears_due_date(client: TestClient):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    created = client.post("/tasks", json={"title": "late", "due_date": yesterday}).json()

    r = client.patch(f"/tasks/{created['id']}", json={"due_date": None})
    assert r.status_code == 200
    body = r.json()
    assert body["due_date"] is None
    assert body["is_overdue"] is False


def test_list_tasks_filter_by_overdue_returns_only_matches(client: TestClient):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    late = client.post("/tasks", json={"title": "late", "due_date": yesterday}).json()
    finished = client.post("/tasks", json={"title": "finished", "due_date": yesterday}).json()
    client.patch(f"/tasks/{finished['id']}", json={"status": "InProgress"})
    client.patch(f"/tasks/{finished['id']}", json={"status": "Done"})
    upcoming = client.post("/tasks", json={"title": "upcoming", "due_date": "2030-01-15"}).json()

    r = client.get("/tasks", params={"overdue": "true"})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [late["id"]]

    r = client.get("/tasks", params={"overdue": "false"})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [finished["id"], upcoming["id"]]

    r = client.get("/tasks")
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [late["id"], finished["id"], upcoming["id"]]


def test_list_tasks_invalid_overdue_returns_422(client: TestClient):
    r = client.get("/tasks", params={"overdue": "banana"})
    assert r.status_code == 422


# ----------------------------------------------------------------------- Tags

def test_create_task_with_tags_returns_normalized_deduped_tags(client: TestClient):
    r = client.post("/tasks", json={"title": "tagged", "tags": ["Bug", " bug ", "Backend"]})
    assert r.status_code == 201
    body = r.json()
    assert set(body) == RESPONSE_FIELDS
    assert body["tags"] == ["bug", "backend"]


def test_create_task_without_tags_returns_empty_tag_list(client: TestClient):
    r = client.post("/tasks", json={"title": "untagged"})
    assert r.status_code == 201
    assert r.json()["tags"] == []


def test_create_task_blank_tag_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "x", "tags": ["bug", "  "]})
    assert r.status_code == 422


def test_create_task_too_many_tags_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "x", "tags": [f"tag{n}" for n in range(11)]})
    assert r.status_code == 422


def test_create_task_tag_too_long_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "x", "tags": ["a" * 31]})
    assert r.status_code == 422


def test_create_task_tag_with_comma_returns_422(client: TestClient):
    r = client.post("/tasks", json={"title": "T", "tags": ["a,b"]})
    assert r.status_code == 422
    assert "commas" in r.text


@pytest.mark.parametrize("bad_tags", ["bug", [1, 2]])
def test_create_task_tags_wrong_type_returns_422(client: TestClient, bad_tags):
    r = client.post("/tasks", json={"title": "x", "tags": bad_tags})
    assert r.status_code == 422


def test_patch_tags_returns_replaced_tags(client: TestClient):
    created = client.post("/tasks", json={"title": "tagged", "tags": ["bug"]}).json()

    r = client.patch(f"/tasks/{created['id']}", json={"tags": ["Frontend"]})
    assert r.status_code == 200
    assert r.json()["tags"] == ["frontend"]


def test_patch_tags_empty_list_clears_tags(client: TestClient):
    created = client.post("/tasks", json={"title": "tagged", "tags": ["bug"]}).json()

    r = client.patch(f"/tasks/{created['id']}", json={"tags": []})
    assert r.status_code == 200
    assert r.json()["tags"] == []


def test_patch_tags_null_clears_tags(client: TestClient):
    created = client.post("/tasks", json={"title": "T", "tags": ["bug"]}).json()
    r = client.patch(f"/tasks/{created['id']}", json={"tags": None})
    assert r.status_code == 200
    assert r.json()["tags"] == []


def test_patch_other_field_preserves_tags(client: TestClient):
    created = client.post("/tasks", json={"title": "tagged", "tags": ["bug", "backend"]}).json()

    r = client.patch(f"/tasks/{created['id']}", json={"title": "Renamed"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Renamed"
    assert body["tags"] == ["bug", "backend"]


def test_list_tasks_filter_by_tag_returns_only_matches(client: TestClient):
    bug = client.post("/tasks", json={"title": "bug", "tags": ["bug", "backend"]}).json()
    client.post("/tasks", json={"title": "ui", "tags": ["frontend"]})
    client.post("/tasks", json={"title": "plain"})

    r = client.get("/tasks", params={"tag": "bug"})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [bug["id"]]

    r = client.get("/tasks", params={"tag": "BUG"})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [bug["id"]]

    r = client.get("/tasks", params={"tag": "nothing"})
    assert r.status_code == 200
    assert r.json() == []


def test_list_tasks_empty_tag_returns_422(client: TestClient):
    r = client.get("/tasks", params={"tag": ""})
    assert r.status_code == 422


def test_list_tasks_filter_by_tag_and_overdue_returns_only_matches(client: TestClient):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    overdue_payload = {"title": "late", "due_date": yesterday, "tags": ["bug"]}
    late = client.post("/tasks", json=overdue_payload).json()
    client.post("/tasks", json={"title": "upcoming", "due_date": "2030-01-15", "tags": ["bug"]})

    r = client.get("/tasks", params={"tag": "bug", "overdue": "true"})
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [late["id"]]
