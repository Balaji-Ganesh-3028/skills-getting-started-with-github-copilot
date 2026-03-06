"""
Integration tests for Mergington High School Activities API

Tests use the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and client
- Act: Execute the API call
- Assert: Verify the response
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a FastAPI test client for each test"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for activity_name in expected_activities:
            assert activity_name in data

    def test_get_activities_has_correct_schema(self, client):
        """Test that each activity has the correct schema"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"

    def test_get_activities_chess_club_details(self, client):
        """Test that Chess Club has correct initial details"""
        # Arrange
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule = "Fridays, 3:30 PM - 5:00 PM"
        expected_max = 12
        expected_initial_participants = 2

        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]

        # Assert
        assert response.status_code == 200
        assert chess_club["description"] == expected_description
        assert chess_club["schedule"] == expected_schedule
        assert chess_club["max_participants"] == expected_max
        assert len(chess_club["participants"]) == expected_initial_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful_with_available_spots(self, client):
        """Test successful signup when activity has available spots"""
        # Arrange
        activity_name = "Chess Club"
        email = "alice@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "bob@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert signup_response.status_code == 200
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert email in final_response.json()[activity_name]["participants"]

    def test_signup_duplicate_email_returns_error(self, client):
        """Test that trying to signup twice for same activity returns 400 error"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up for Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404 error"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_to_full_activity_returns_error(self, client):
        """Test that trying to signup for full activity returns 400 error"""
        # Arrange
        activity_name = "Gym Class"
        
        # First, get initial participant count and max
        activities_response = client.get("/activities")
        gym_activity = activities_response.json()[activity_name]
        max_participants = gym_activity["max_participants"]
        current_count = len(gym_activity["participants"])
        
        # Sign up students until the activity is full
        for i in range(max_participants - current_count):
            email = f"new_student_{i}@mergington.edu"
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Try to signup when activity is full
        final_email = "final_student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": final_email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()

    def test_signup_activity_name_with_special_characters(self, client):
        """Test that signup works with activity names that need URL encoding"""
        # Arrange
        activity_name = "Programming Class"  # Contains space
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
