"""Integration checks use a disposable database, never the feedback database."""
import os
import unittest
import uuid
from unittest.mock import patch

import psycopg
from psycopg import sql

from dashboard.app import app
from dashboard.stats import get_summary


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name = 'dashboard_test_' + uuid.uuid4().hex
        cls.admin = psycopg.connect(
            host=os.environ['DB_HOST'], port=os.environ['DB_PORT'],
            dbname=os.environ['DB_NAME'], user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'], autocommit=True)
        cls.admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cls.name)))
        cls.env = patch.dict(os.environ, DB_NAME=cls.name)
        cls.env.start()
        cls.writer = psycopg.connect(
            host=os.environ['DB_HOST'], port=os.environ['DB_PORT'],
            dbname=cls.name, user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'], autocommit=True)
        cls.writer.execute('CREATE TABLE public.feedback (id SERIAL PRIMARY KEY, difficulty INTEGER, topic VARCHAR(32))')
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.writer.close()
        cls.env.stop()
        cls.admin.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(cls.name)))
        cls.admin.close()

    def setUp(self):
        self.writer.execute('TRUNCATE public.feedback')

    def test_empty_database(self):
        result = get_summary()
        self.assertEqual(result['total'], 0)
        self.assertIsNone(result['average'])
        self.assertEqual([count for _, count in result['topics']], [0, 0, 0, 0])
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No data yet', response.data)

    def test_sample_and_refresh(self):
        self.writer.execute("INSERT INTO public.feedback (difficulty, topic) VALUES (1,'Docker'),(3,'Docker'),(5,'Kubernetes')")
        result = get_summary()
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['average'], '3.00')
        self.assertEqual(dict(result['topics']), {'Virtual Machine': 0, 'Docker': 2, 'Kubernetes': 1, 'Serverless': 0})
        self.assertIn(b'3.00', self.client.get('/').data)
        self.writer.execute("INSERT INTO public.feedback (difficulty, topic) VALUES (2,'Serverless')")
        response = self.client.get('/')
        self.assertIn(b'2.75', response.data)
        self.assertIn(b'id="total">4<', response.data)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.client.post('/').status_code, 405)

    def test_real_connection_failure(self):
        with patch.dict(os.environ, DB_PORT='1'):
            response = self.client.get('/')
        self.assertEqual(response.status_code, 503)
        self.assertIn(b'temporarily unavailable', response.data)
        self.assertNotIn(b'id="total"', response.data)
        self.assertNotIn(os.environ['DB_PASSWORD'].encode(), response.data)
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_missing_configuration(self):
        with patch.dict(os.environ, DB_PASSWORD=''):
            self.assertEqual(self.client.get('/').status_code, 503)


if __name__ == '__main__':
    unittest.main()
