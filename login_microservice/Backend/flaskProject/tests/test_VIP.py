import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from flask import session, jsonify
from flaskProject.main import app

class TestCalculateVIP(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        app.secret_key = "fake key"

    @patch("flaskProject.main.get_userstories_for_milestones")
    @patch("flaskProject.main.get_business_value_id")
    @patch("flaskProject.main.get_custom_attribute_values")
    @patch("flaskProject.main.get_user_story_business_value_map")
    @patch("flaskProject.main.get_milestones_by_sprint")
    @patch("flaskProject.main.get_user_story_start_date")
    def test_calculate_VIP_success(self, mock_get_user_story_start_date, mock_get_milestones_by_sprint, mock_get_user_story_business_value_map, mock_get_custom_attribute_values, mock_get_business_value_id, mock_get_userstories_for_milestones):
        # Mocking necessary data
        session['auth_token'] = 'fake_auth_token'
        session['project_id'] = 'fake_project_id'
        session['sprint_id'] = '1'
        user_stories = [
            {"id": "1", "total_points": 5, "finish_date": "2024-01-05"},
            {"id": "2", "total_points": 8, "finish_date": "2024-01-08"}
        ]
        mock_get_userstories_for_milestones.return_value = [user_stories]
        mock_get_milestones_by_sprint.return_value = {
            "estimated_start": "2024-01-01",
            "estimated_finish": "2024-01-10"
        }
        mock_get_user_story_business_value_map.return_value = {
            "1": 3,
            "2": 5
        }
        mock_get_custom_attribute_values.return_value = {}
        mock_get_business_value_id.return_value = 1
        mock_get_user_story_start_date.return_value = {"1": datetime(2024, 1, 1), "2": datetime(2024, 1, 2)}

        # Making request to the route
        response = self.app.get('/VIPC')

        # Asserting response
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 10)  

    @patch("flaskProject.main.get_userstories_for_milestones")
    def test_calculate_VIP_no_auth_token(self, mock_get_userstories_for_milestones):
        session.pop('auth_token', None)

        response = self.app.get('/VIPC')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://localhost/')

    # Add more test cases as needed

if __name__ == '__main__':
    unittest.main()
