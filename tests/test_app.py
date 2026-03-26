import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

@pytest.fixture(autouse=True)
def reset_activities():
    """Snapshot and restore the in-memory activities between tests."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


# ── GET /activities ──────────────────────────────────────────────

class TestGetActivities:
    def test_returns_all_activities(self):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_has_expected_fields(self):
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ── POST /activities/{name}/signup ───────────────────────────────

class TestSignup:
    def test_signup_success(self):
        response = client.post(
            "/activities/Chess Club/signup?email=new-student@mergington.edu"
        )
        assert response.status_code == 200
        assert "new-student@mergington.edu" in response.json()["message"]

        # Verify participant was added
        data = client.get("/activities").json()
        assert "new-student@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_duplicate(self):
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_unknown_activity(self):
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ── POST /activities/{name}/unregister ───────────────────────────

class TestUnregister:
    def test_unregister_success(self):
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

        # Verify participant was removed
        data = client.get("/activities").json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_not_enrolled(self):
        response = client.post(
            "/activities/Chess Club/unregister?email=nobody@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_unknown_activity(self):
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
