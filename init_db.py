from app import app
from models import db, User, Doctor
from datetime import datetime

def init_database():
    """Initialize database with admin user and sample doctors"""
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            name='Admin',
            email='admin@hospital.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample doctors
        doctors = [
            Doctor(name='Dr. John Smith', specialization='Cardiologist'),
            Doctor(name='Dr. Sarah Johnson', specialization='Pediatrician'),
            Doctor(name='Dr. Michael Brown', specialization='Orthopedic'),
            Doctor(name='Dr. Emily Davis', specialization='Dermatologist'),
            Doctor(name='Dr. Robert Wilson', specialization='Neurologist'),
        ]
        
        for doctor in doctors:
            db.session.add(doctor)
        
        # Commit changes
        db.session.commit()
        
        print("✅ Database initialized successfully!")
        print("✅ Admin user created:")
        print("   Email: admin@hospital.com")
        print("   Password: admin123")
        print(f"✅ {len(doctors)} sample doctors added")

if __name__ == '__main__':
    init_database()
