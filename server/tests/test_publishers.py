import unittest
import json
from typing import Dict, List, Any
from flask import Flask, Response
from models import Publisher, db, init_db
from routes.publishers import publishers_bp

class TestPublishersRoutes(unittest.TestCase):
    # Test data
    TEST_DATA: Dict[str, Any] = {
        "publishers": [
            {"name": "DevGames Inc", "description": "Leading developer of programming-themed games"},
            {"name": "Scrum Masters", "description": "Agile game development studio"},
            {"name": "Code Crafters", "description": "Creating engaging developer experiences"}
        ]
    }
    
    # API paths
    PUBLISHERS_API_PATH: str = '/api/publishers'

    def setUp(self) -> None:
        """Set up test database and seed data"""
        # Create a fresh Flask app for testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Register the publishers blueprint
        self.app.register_blueprint(publishers_bp)
        
        # Initialize the test client
        self.client = self.app.test_client()
        
        # Initialize in-memory database for testing
        init_db(self.app, testing=True)
        
        # Create tables and seed data
        with self.app.app_context():
            db.create_all()
            self._seed_test_data()

    def tearDown(self) -> None:
        """Clean up test database and ensure proper connection closure"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def _seed_test_data(self) -> None:
        """Helper method to seed test data"""
        # Create test publishers
        publishers = [
            Publisher(**publisher_data) for publisher_data in self.TEST_DATA["publishers"]
        ]
        db.session.add_all(publishers)
        db.session.commit()

    def test_get_publishers(self) -> None:
        """Test retrieving all publishers"""
        response: Response = self.client.get(self.PUBLISHERS_API_PATH)
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        data: List[Dict[str, Any]] = json.loads(response.data)
        
        # Verify we got all publishers
        self.assertEqual(len(data), len(self.TEST_DATA["publishers"]))
        
        # Verify structure of response (only id and name)
        for publisher in data:
            self.assertIn('id', publisher)
            self.assertIn('name', publisher)
            # Ensure only id and name are returned
            self.assertEqual(len(publisher.keys()), 2)
        
        # Verify publisher names match
        publisher_names = {p['name'] for p in data}
        expected_names = {p['name'] for p in self.TEST_DATA["publishers"]}
        self.assertEqual(publisher_names, expected_names)

    def test_get_publishers_empty(self) -> None:
        """Test retrieving publishers when none exist"""
        # Clear all publishers
        with self.app.app_context():
            db.session.query(Publisher).delete()
            db.session.commit()
        
        response: Response = self.client.get(self.PUBLISHERS_API_PATH)
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        data: List[Dict[str, Any]] = json.loads(response.data)
        
        # Verify empty array
        self.assertEqual(len(data), 0)
        self.assertEqual(data, [])

if __name__ == '__main__':
    unittest.main()
