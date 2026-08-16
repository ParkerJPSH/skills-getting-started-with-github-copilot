"""
Test suite for Mergington High School Activities API

Uses AAA (Arrange-Act-Assert) pattern for all tests:
- Arrange: Set up test data and fixtures
- Act: Execute the API call being tested
- Assert: Verify the response and side effects
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


def _get_original_activities():
    """Get a deep copy of the original activities data"""
    return copy.deepcopy(dict(activities))


@pytest.fixture(autouse=False)
def client():
    """
    Fixture that provides a test client with a fresh copy of activities data
    for each test to ensure isolation and prevent test interdependencies.
    
    Arrange: Initialize TestClient and reset app state
    """
    # Get a fresh copy of original activities for this test
    original_activities = _get_original_activities()
    
    # Reset activities to original state - use assignment to avoid reference issues
    activities.clear()
    for activity_name, activity_data in original_activities.items():
        activities[activity_name] = copy.deepcopy(activity_data)
    
    yield TestClient(app)
    
    # Reset after test (for cleanup between tests) - use assignment to avoid reference issues
    activities.clear()
    for activity_name, activity_data in original_activities.items():
        activities[activity_name] = copy.deepcopy(activity_data)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """
        Test that GET /activities returns all activities with correct structure
        
        Arrange: Test client with sample activities
        Act: Call GET /activities
        Assert: Status 200, activities in response, correct keys present
        """
        # Arrange
        # (client fixture already set up)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify structure of each activity
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_contains_chess_club(self, client):
        """
        Test that Chess Club is in the activities list with correct participants
        
        Arrange: Test client with activities
        Act: Call GET /activities and find Chess Club
        Assert: Chess Club exists with michael and daniel as participants
        """
        # Arrange
        # (client fixture already set up)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "Chess Club" in data
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
        assert chess_club["max_participants"] == 12


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """
        Test successful signup for an activity
        
        Arrange: Test client, new email not yet registered
        Act: POST /activities/Chess Club/signup with new email
        Assert: Status 200, success message, participant added to list
        """
        # Arrange
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]
        assert new_email in activities["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """
        Test signup to non-existent activity returns 404
        
        Arrange: Test client, invalid activity name
        Act: POST /activities/FakeActivity/signup
        Assert: Status 404, error detail in response
        """
        # Arrange
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/FakeActivity/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_duplicate_participant(self, client):
        """
        Test signup fails when student already registered (duplicate)
        
        Arrange: Test client, email already in Chess Club participants
        Act: POST /activities/Chess Club/signup with michael@mergington.edu
        Assert: Status 400, error about already signed up
        """
        # Arrange
        existing_email = "michael@mergington.edu"
        # Verify email is in participants
        assert existing_email in activities["Chess Club"]["participants"]
        
        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_adds_participant_to_correct_activity(self, client):
        """
        Test that signup adds participant only to the correct activity
        
        Arrange: Test client, new email, two activities (Chess Club, Programming Class)
        Act: Signup to Chess Club
        Assert: Participant added to Chess Club but not to Programming Class
        """
        # Arrange
        new_email = "testuser@mergington.edu"
        original_chess_count = len(activities["Chess Club"]["participants"])
        original_prog_count = len(activities["Programming Class"]["participants"])
        
        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert new_email in activities["Chess Club"]["participants"]
        assert new_email not in activities["Programming Class"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == original_chess_count + 1
        assert len(activities["Programming Class"]["participants"]) == original_prog_count


class TestRemoveParticipant:
    """Tests for POST /activities/{activity_name}/remove endpoint"""
    
    def test_remove_participant_success(self, client):
        """
        Test successful removal of participant from activity
        
        Arrange: Test client, michael is in Chess Club
        Act: POST /activities/Chess Club/remove with michael's email
        Assert: Status 200, success message, participant removed from list
        """
        # Arrange
        email = "michael@mergington.edu"
        assert email in activities["Chess Club"]["participants"]
        original_count = len(activities["Chess Club"]["participants"])
        
        # Act
        response = client.post(
            "/activities/Chess Club/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == original_count - 1
    
    def test_remove_activity_not_found(self, client):
        """
        Test remove from non-existent activity returns 404
        
        Arrange: Test client, invalid activity name
        Act: POST /activities/FakeActivity/remove
        Assert: Status 404, error detail in response
        """
        # Arrange
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/FakeActivity/remove",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_remove_participant_not_in_activity(self, client):
        """
        Test remove fails when student not in activity (not a member)
        
        Arrange: Test client, email not in Chess Club participants
        Act: POST /activities/Chess Club/remove with non-member email
        Assert: Status 400, error about not being signed up
        """
        # Arrange
        non_member_email = "nonmember@mergington.edu"
        assert non_member_email not in activities["Chess Club"]["participants"]
        
        # Act
        response = client.post(
            "/activities/Chess Club/remove",
            params={"email": non_member_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()
    
    def test_remove_decreases_participant_count(self, client):
        """
        Test that removing participant decreases count correctly
        
        Arrange: Test client, Chess Club has multiple participants
        Act: Remove one participant
        Assert: Count decreased by exactly 1, other participants still present
        """
        # Arrange
        email_to_remove = "michael@mergington.edu"
        other_email = "daniel@mergington.edu"
        original_count = len(activities["Chess Club"]["participants"])
        
        # Act
        response = client.post(
            "/activities/Chess Club/remove",
            params={"email": email_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        new_count = len(activities["Chess Club"]["participants"])
        assert new_count == original_count - 1
        assert other_email in activities["Chess Club"]["participants"]


class TestSignupAndRemoveIntegration:
    """Integration tests for signup and remove together"""
    
    def test_signup_then_remove_participant(self, client):
        """
        Test signup followed by remove returns participant to original state
        
        Arrange: Test client, new email, original participant count
        Act: Signup, then remove same email
        Assert: Participant count returns to original, email not in list
        """
        # Arrange
        new_email = "integration@mergington.edu"
        original_count = len(activities["Chess Club"]["participants"])
        
        # Act - Signup
        signup_response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        
        # Assert signup succeeded
        assert signup_response.status_code == 200
        assert new_email in activities["Chess Club"]["participants"]
        
        # Act - Remove
        remove_response = client.post(
            "/activities/Chess Club/remove",
            params={"email": new_email}
        )
        
        # Assert remove succeeded and state is restored
        assert remove_response.status_code == 200
        assert new_email not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == original_count
