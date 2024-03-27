from main import app
import unittest
from flask import session, request, render_template
from unittest.mock import patch

class TestBusinessValueAuc(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        app.secret_key = "fake_key"

    @patch('main.get_number_of_milestones')
    @patch('main.get_business_value_data_for_sprint')
    def test_get_business_value_auc_delta(self, mock_get_bv_data, mock_get_num_milestones):
        session['auth_token'] = "fake_auth_token"
        session['project_id'] = 'fake_project_id'
        session['sprint_id'] = 'fake_sprint_id'

        mock_get_num_milestones.return_value = ({'sprint1': 'id1', 'sprint2': 'id2'}, 2)

        mock_get_bv_data.side_effect = [
            ({'item1': 10}, {'item1': 20}),  
            ({'item2': 5}, {'item2': 15})    
        ]

        with app.test_request_context('/business-value-auc'):
            with self.app as client:
                response = client.get('/business-value-auc')
                self.assertEqual(response.status_code, 200)
                
        mock_get_bv_data.side_effect = [
            ({'item1': 0}, {'item1': 20}), 
            ({'item2': 5}, {'item2': 15}) 
        ]

        with app.test_request_context('/business-value-auc'):
            with self.app as client:
                response = client.get('/business-value-auc')
                self.assertEqual(response.status_code, 200)

        session['sprint_id'] = 'id1'  

        with app.test_request_context('/business-value-auc'):
            with self.app as client:
                response = client.get('/business-value-auc')
                self.assertEqual(response.status_code, 200)
