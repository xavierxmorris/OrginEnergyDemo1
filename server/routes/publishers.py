from flask import jsonify, Response, Blueprint
from models import db, Publisher
from sqlalchemy.orm import Query

# Create a Blueprint for publishers routes
publishers_bp = Blueprint('publishers', __name__)

def get_publishers_base_query() -> Query:
    """Base query for retrieving publishers.
    
    Returns:
        Query: SQLAlchemy query object for publishers
    """
    return db.session.query(Publisher)

@publishers_bp.route('/api/publishers', methods=['GET'])
def get_publishers() -> Response:
    """Get all publishers with their id and name.
    
    Returns:
        Response: JSON array of publishers with id and name fields
    """
    # Use the base query for all publishers
    publishers_query = get_publishers_base_query().all()
    
    # Convert the results to a simplified dict with only id and name
    publishers_list = [{'id': publisher.id, 'name': publisher.name} for publisher in publishers_query]
    
    return jsonify(publishers_list)
