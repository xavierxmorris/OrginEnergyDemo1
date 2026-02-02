import unittest
import json
from typing import Dict, List, Any, Optional
from flask import Flask, Response
from models import Game, Publisher, Category, db, init_db
from routes.games import games_bp

class TestGamesRoutes(unittest.TestCase):
    # Test data as complete objects
    TEST_DATA: Dict[str, Any] = {
        "publishers": [
            {"name": "DevGames Inc"},
            {"name": "Scrum Masters"}
        ],
        "categories": [
            {"name": "Strategy"},
            {"name": "Card Game"}
        ],
        "games": [
            {
                "title": "Pipeline Panic",
                "description": "Build your DevOps pipeline before chaos ensues",
                "publisher_index": 0,
                "category_index": 0,
                "star_rating": 4.5
            },
            {
                "title": "Agile Adventures",
                "description": "Navigate your team through sprints and releases",
                "publisher_index": 1,
                "category_index": 1,
                "star_rating": 4.2
            }
        ]
    }
    
    # API paths
    GAMES_API_PATH: str = '/api/games'

    def setUp(self) -> None:
        """Set up test database and seed data"""
        # Create a fresh Flask app for testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Register the games blueprint
        self.app.register_blueprint(games_bp)
        
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
        
        # Create test categories
        categories = [
            Category(**category_data) for category_data in self.TEST_DATA["categories"]
        ]
        db.session.add_all(categories)
        
        # Commit to get IDs
        db.session.commit()
        
        # Create test games
        games = []
        for game_data in self.TEST_DATA["games"]:
            game_dict = game_data.copy()
            publisher_index = game_dict.pop("publisher_index")
            category_index = game_dict.pop("category_index")
            
            games.append(Game(
                **game_dict,
                publisher=publishers[publisher_index],
                category=categories[category_index]
            ))
            
        db.session.add_all(games)
        db.session.commit()

    def _get_response_data(self, response: Response) -> Any:
        """Helper method to parse response data"""
        return json.loads(response.data)

    def test_get_games_success(self) -> None:
        """Test successful retrieval of multiple games"""
        # Act
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), len(self.TEST_DATA["games"]))
        
        # Verify all games using loop instead of manual testing
        for i, game_data in enumerate(data):
            test_game = self.TEST_DATA["games"][i]
            test_publisher = self.TEST_DATA["publishers"][test_game["publisher_index"]]
            test_category = self.TEST_DATA["categories"][test_game["category_index"]]
            
            self.assertEqual(game_data['title'], test_game["title"])
            self.assertEqual(game_data['publisher']['name'], test_publisher["name"])
            self.assertEqual(game_data['category']['name'], test_category["name"])
            self.assertEqual(game_data['starRating'], test_game["star_rating"])

    def test_get_games_structure(self) -> None:
        """Test the response structure for games"""
        # Act
        response = self.client.get(self.GAMES_API_PATH)
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(self.TEST_DATA["games"]))
        
        required_fields = ['id', 'title', 'description', 'publisher', 'category', 'starRating']
        for field in required_fields:
            self.assertIn(field, data[0])

    def test_get_game_by_id_success(self) -> None:
        """Test successful retrieval of a single game by ID"""
        # Get the first game's ID from the list endpoint
        response = self.client.get(self.GAMES_API_PATH)
        games = self._get_response_data(response)
        game_id = games[0]['id']
        
        # Act
        response = self.client.get(f'{self.GAMES_API_PATH}/{game_id}')
        data = self._get_response_data(response)
        
        # Assert
        first_game = self.TEST_DATA["games"][0]
        first_publisher = self.TEST_DATA["publishers"][first_game["publisher_index"]]
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], first_game["title"])
        self.assertEqual(data['publisher']['name'], first_publisher["name"])
        
    def test_get_game_by_id_not_found(self) -> None:
        """Test retrieval of a non-existent game by ID"""
        # Act
        response = self.client.get(f'{self.GAMES_API_PATH}/999')
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Game not found")

    def test_create_game_success(self) -> None:
        """Test successful creation of a new game"""
        # Arrange - Get publisher and category IDs
        with self.app.app_context():
            publishers = db.session.query(Publisher).all()
            categories = db.session.query(Category).all()
            
            new_game_data = {
                "title": "Test Game",
                "description": "This is a test game description",
                "publisher_id": publishers[0].id,
                "category_id": categories[0].id,
                "star_rating": 4.8
            }
        
        # Act
        response = self.client.post(
            self.GAMES_API_PATH,
            data=json.dumps(new_game_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['title'], new_game_data['title'])
        self.assertEqual(data['description'], new_game_data['description'])
        self.assertEqual(data['starRating'], new_game_data['star_rating'])
        self.assertEqual(data['publisher']['id'], new_game_data['publisher_id'])
        self.assertEqual(data['category']['id'], new_game_data['category_id'])
        self.assertIsNotNone(data['id'])

    def test_create_game_missing_fields(self) -> None:
        """Test game creation with missing required fields"""
        # Act
        response = self.client.post(
            self.GAMES_API_PATH,
            data=json.dumps({"title": "Incomplete Game"}),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_create_game_no_data(self) -> None:
        """Test game creation with no data provided"""
        # Act
        response = self.client.post(
            self.GAMES_API_PATH,
            data=json.dumps(None),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], "No data provided")

    def test_create_game_invalid_publisher(self) -> None:
        """Test game creation with non-existent publisher"""
        # Arrange
        with self.app.app_context():
            categories = db.session.query(Category).all()
            
            new_game_data = {
                "title": "Test Game",
                "description": "This is a test game description",
                "publisher_id": 999,
                "category_id": categories[0].id
            }
        
        # Act
        response = self.client.post(
            self.GAMES_API_PATH,
            data=json.dumps(new_game_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Publisher not found")

    def test_create_game_invalid_category(self) -> None:
        """Test game creation with non-existent category"""
        # Arrange
        with self.app.app_context():
            publishers = db.session.query(Publisher).all()
            
            new_game_data = {
                "title": "Test Game",
                "description": "This is a test game description",
                "publisher_id": publishers[0].id,
                "category_id": 999
            }
        
        # Act
        response = self.client.post(
            self.GAMES_API_PATH,
            data=json.dumps(new_game_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Category not found")

    def test_create_game_invalid_title(self) -> None:
        """Test game creation with invalid title (too short)"""
        # Arrange
        with self.app.app_context():
            publishers = db.session.query(Publisher).all()
            categories = db.session.query(Category).all()
            
            new_game_data = {
                "title": "A",
                "description": "This is a test game description",
                "publisher_id": publishers[0].id,
                "category_id": categories[0].id
            }
        
        # Act
        response = self.client.post(
            self.GAMES_API_PATH,
            data=json.dumps(new_game_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

    def test_update_game_success(self) -> None:
        """Test successful update of an existing game"""
        # Arrange - Get an existing game
        with self.app.app_context():
            games = db.session.query(Game).all()
            game_id = games[0].id
        
        update_data = {
            "title": "Updated Title",
            "description": "Updated description for the game"
        }
        
        # Act
        response = self.client.put(
            f'{self.GAMES_API_PATH}/{game_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], update_data['title'])
        self.assertEqual(data['description'], update_data['description'])
        self.assertEqual(data['id'], game_id)

    def test_update_game_partial(self) -> None:
        """Test partial update of a game (only some fields)"""
        # Arrange - Get an existing game
        with self.app.app_context():
            games = db.session.query(Game).all()
            game_id = games[0].id
            original_description = games[0].description
        
        update_data = {
            "title": "Partially Updated Title"
        }
        
        # Act
        response = self.client.put(
            f'{self.GAMES_API_PATH}/{game_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], update_data['title'])
        self.assertEqual(data['description'], original_description)

    def test_update_game_not_found(self) -> None:
        """Test update of a non-existent game"""
        # Arrange
        update_data = {
            "title": "Updated Title"
        }
        
        # Act
        response = self.client.put(
            f'{self.GAMES_API_PATH}/999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Game not found")

    def test_update_game_no_data(self) -> None:
        """Test update with no data provided"""
        # Arrange - Get an existing game
        with self.app.app_context():
            games = db.session.query(Game).all()
            game_id = games[0].id
        
        # Act
        response = self.client.put(
            f'{self.GAMES_API_PATH}/{game_id}',
            data=json.dumps(None),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], "No data provided")

    def test_update_game_invalid_category(self) -> None:
        """Test update with non-existent category"""
        # Arrange - Get an existing game
        with self.app.app_context():
            games = db.session.query(Game).all()
            game_id = games[0].id
        
        update_data = {
            "category_id": 999
        }
        
        # Act
        response = self.client.put(
            f'{self.GAMES_API_PATH}/{game_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Category not found")

    def test_update_game_invalid_publisher(self) -> None:
        """Test update with non-existent publisher"""
        # Arrange - Get an existing game
        with self.app.app_context():
            games = db.session.query(Game).all()
            game_id = games[0].id
        
        update_data = {
            "publisher_id": 999
        }
        
        # Act
        response = self.client.put(
            f'{self.GAMES_API_PATH}/{game_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Publisher not found")

    def test_delete_game_success(self) -> None:
        """Test successful deletion of a game"""
        # Arrange - Get an existing game
        with self.app.app_context():
            games = db.session.query(Game).all()
            game_id = games[0].id
        
        # Act
        response = self.client.delete(f'{self.GAMES_API_PATH}/{game_id}')
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], "Game deleted successfully")
        
        # Verify game is deleted
        with self.app.app_context():
            deleted_game = db.session.query(Game).filter(Game.id == game_id).first()
            self.assertIsNone(deleted_game)

    def test_delete_game_not_found(self) -> None:
        """Test deletion of a non-existent game"""
        # Act
        response = self.client.delete(f'{self.GAMES_API_PATH}/999')
        data = self._get_response_data(response)
        
        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], "Game not found")

if __name__ == '__main__':
    unittest.main()