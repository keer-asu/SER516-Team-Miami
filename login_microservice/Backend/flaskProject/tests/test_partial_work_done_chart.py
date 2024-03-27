import unittest
from unittest.mock import patch, MagicMock
from flask import session
from flaskProject.main import app

class TestPartialWorkDoneChart(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    @patch('main.get_milestones_by_sprint')
    @patch('main.get_tasks')
    def test_partial_work_done_chart_success(self, mock_get_tasks, mock_get_milestones_by_sprint):
        session['auth_token'] = 'fake_auth_token'
        session['project_id'] = 'fake_project_id'
        session['sprint_selected'] = '1'

        mock_get_milestones_by_sprint.return_value = {
            "user_stories": [
                {"id": "1", "total_points": 5, "created_date": "2024-01-01", "finish_date": "2024-01-05"},
                {"id": "2", "total_points": 8, "created_date": "2024-01-02", "finish_date": "2024-01-08"}
            ],
            "estimated_start": "2024-01-01",
            "estimated_finish": "2024-01-10"
        }
        mock_get_tasks.return_value = [
            {"user_story": "1", "status_extra_info": {"is_closed": True}, "finished_date": "2024-01-05"},
            {"user_story": "2", "status_extra_info": {"is_closed": True}, "finished_date": "2024-01-08"}
        ]

        response = self.app.get('/fake_project_id/1/partial-work-done-chart')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("total_story_points", data)
        self.assertIn("x_axis", data)
        self.assertIn("y_axis", data)
        self.assertIn("ideal_projection", data)
        self.assertIn("actual_projection", data)
        self.assertEqual(len(data["x_axis"]), 10)

    @patch('main.get_milestones_by_sprint')
    def test_partial_work_done_chart_no_auth_token(self, mock_get_milestones_by_sprint):
        session.pop('auth_token', None)

        response = self.app.get('/fake_project_id/1/partial-work-done-chart')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, 'http://localhost/')

    def test_no_project_id_in_session(self):
        session['auth_token'] = 'fake_auth_token'
        session.pop('project_id', None)

        response = self.app.get('/fake_project_id/1/partial-work-done-chart')

        self.assertEqual(response.status_code, 200)  

    def test_no_sprint_id_in_session(self):
        session['auth_token'] = 'fake_auth_token'
        session.pop('sprint_selected', None)

        response = self.app.get('/fake_project_id/1/partial-work-done-chart')

        self.assertEqual(response.status_code, 200)  

if __name__ == '__main__':
    unittest.main()
