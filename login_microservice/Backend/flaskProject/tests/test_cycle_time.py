from main import app
import unittest
from flask import Flask, request, session, redirect, jsonify
from unittest.mock import patch
import json

class TestCycleTime(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        app.secret_key = "fake_key"

    @patch('main.get_one_closed_task')
    @patch('main.get_task_history')
    def test_cycle_time_graph(self, fake_get_task_history, fake_get_one_closed_task):
        
        fake_get_one_closed_task.return_value = [
            {
                "id": 1,
                "subject": "fake_task",
                "created_date": "2021-01-01",
                "finished_date": "2021-01-10"
            }
        ]
        fake_get_task_history.return_value = (9, 1)
        with app.test_request_context('/cycle-time-graph'):
            with self.app as client:
                session['auth_token'] = "fake_auth_token"
                session['project_id'] = 'fake_project_id'
                response = client.post('/cycle-time-graph', json={'closed_tasks_ids': [1]})
                self.assertEqual(response.status_code, 200)

                expected_result = [{"task_id": 1, "cycle_time": 9}]
                self.assertEqual(json.loads(response.data), expected_result)

    def test_no_auth_token(self):
        with app.test_request_context('/cycle-time-graph'):
            with self.app as client:
                session.clear()  
                response = client.post('/cycle-time-graph', json={'closed_tasks_ids': [1]})
                self.assertEqual(response.status_code, 302)  
                self.assertEqual(response.location, 'http://localhost/')  
                
    def test_no_closed_tasks_ids(self):
        with app.test_request_context('/cycle-time-graph'):
            with self.app as client:
                session['auth_token'] = "fake_auth_token"
                session['project_id'] = 'fake_project_id'
                response = client.post('/cycle-time-graph', json={})
                self.assertEqual(response.status_code, 400)  
                
    @patch('main.calculate_cycle_times_for_tasks')
    def test_no_specific_tasks_selected(self, fake_calculate_cycle_times):
        fake_calculate_cycle_times.return_value = []  
        with app.test_request_context('/cycle-time-graph'):
            with self.app as client:
                session['auth_token'] = "fake_auth_token"
                session['project_id'] = 'fake_project_id'
                session['closed_tasks_in_a_sprint'] = [{'ref': 1}, {'ref': 2}]  
                response = client.post('/cycle-time-graph', json={'closed_tasks_ids': [0]})
                self.assertEqual(response.status_code, 200)  
                fake_calculate_cycle_times.assert_called_with(
                    [{'ref': 1}, {'ref': 2}], "fake_auth_token"
                )
                
    @patch('main.calculate_cycle_times_for_tasks')
    def test_specific_tasks_selected(self, fake_calculate_cycle_times):
        fake_calculate_cycle_times.return_value = [{"task_id": 1, "cycle_time": 9}]  
        with app.test_request_context('/cycle-time-graph'):
            with self.app as client:
                session['auth_token'] = "fake_auth_token"
                session['project_id'] = 'fake_project_id'
                session['closed_tasks_in_a_sprint'] = [{'ref': 1}, {'ref': 2}]  
                response = client.post('/cycle-time-graph', json={'closed_tasks_ids': [1]})
                self.assertEqual(response.status_code, 200)  
                fake_calculate_cycle_times.assert_called_with(
                    [{'ref': 1}], "fake_auth_token"
                )

if __name__ == '__main__':
    unittest.main()
