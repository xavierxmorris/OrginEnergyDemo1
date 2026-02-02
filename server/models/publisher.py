from . import db
from .base import BaseModel
from sqlalchemy.orm import validates, relationship

class Publisher(BaseModel):
    __tablename__ = 'publishers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # One-to-many relationship: one publisher has many games
    games = relationship("Game", back_populates="publisher")

    @validates('name')
    def validate_name(self, key, name):
        """
        Validates the publisher name to ensure it meets minimum length requirements.
        
        Args:
            key: The field name being validated
            name: The publisher name value to validate
            
        Returns:
            str: The validated name
            
        Raises:
            ValueError: If name is invalid or too short
        """
        return self.validate_string_length('Publisher name', name, min_length=2)

    @validates('description')
    def validate_description(self, key, description):
        """
        Validates the publisher description to ensure it meets minimum length requirements.
        
        Args:
            key: The field name being validated
            description: The description value to validate
            
        Returns:
            str: The validated description
            
        Raises:
            ValueError: If description is invalid or too short
        """
        return self.validate_string_length('Description', description, min_length=10, allow_none=True)

    def __repr__(self):
        """
        Returns a string representation of the Publisher object.
        
        Returns:
            str: String representation including publisher name
        """
        return f'<Publisher {self.name}>'

    def to_dict(self):
        """
        Converts the Publisher object to a dictionary for JSON serialization.
        
        Returns:
            dict: Dictionary containing publisher data including game count
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'game_count': len(self.games) if self.games else 0
        }