"""
Database initialization and migration utility script.
Run this script to create/update database tables.
"""
import os
from app import app, db

def init_db():
    """Initialize the database tables."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

        # Test connection
        try:
            db.session.execute(db.text('SELECT 1'))
            print("Database connection verified!")
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

if __name__ == '__main__':
    init_db()
