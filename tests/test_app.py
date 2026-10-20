import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)
INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory database before each test"""
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


def test_root_redirects_to_index():
    # Arrange / Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all():
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert len(data) == len(INITIAL_ACTIVITIES)


def test_signup_adds_participant():
    # Arrange
    email = "new@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in activities["Chess Club"]["participants"]


def test_signup_duplicate_is_rejected():
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_unknown_activity_returns_404():
    # Act
    response = client.post("/activities/Unknown/signup", params={"email": "a@mergington.edu"})

    # Assert
    assert response.status_code == 404


def test_signup_full_activity_is_rejected():
    # Arrange
    activity = activities["Chess Club"]
    activity["participants"] = [f"s{i}@mergington.edu" for i in range(activity["max_participants"])]

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": "late@mergington.edu"})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_participant():
    # Arrange
    email = "michael@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/unregister", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_not_signed_up_returns_400():
    # Act
    response = client.delete("/activities/Chess Club/unregister", params={"email": "ghost@mergington.edu"})

    # Assert
    assert response.status_code == 400


def test_unregister_unknown_activity_returns_404():
    # Act
    response = client.delete("/activities/Unknown/unregister", params={"email": "a@mergington.edu"})

    # Assert
    assert response.status_code == 404
