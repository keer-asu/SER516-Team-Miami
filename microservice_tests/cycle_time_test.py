import unittest
from unittest.mock import patch, MagicMock
from Backend.flaskProject.main import app

class CycleTimeTest(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('Backend.flaskProject.main.requests.post')
    def test_ct(self, fake_post):
        with self.app.session_transaction() as fake_session:
            fake_session['auth_token'] = 'fake_auth_token'
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {'data_to_plot': 'fake_data_to_plot'}
        fake_post.return_value = fake_response
        response = self.app.get('/cycle-time-graph')
        self.assertEqual(response.status_code, 200)