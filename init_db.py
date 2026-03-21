from app import app
from models import db, User, Doctor
from datetime import datetime
from models import db, User, Doctor, Announcement

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
            Doctor(name='Dr. John Smith', specialization='Cardiologist', 
                   available_days='Mon-Fri', available_time='9:00 AM - 5:00 PM'),
            Doctor(name='Dr. Sarah Johnson', specialization='Pediatrician',
                   available_days='Mon/Wed/Fri', available_time='10:00 AM - 2:00 PM'),
            Doctor(name='Dr. Michael Brown', specialization='Orthopedic',
                   available_days='Tue-Sat', available_time='8:00 AM - 12:00 PM'),
            Doctor(name='Dr. Emily Davis', specialization='Dermatologist',
                   available_days='Mon-Thu', available_time='1:00 PM - 6:00 PM'),
            Doctor(name='Dr. Robert Wilson', specialization='Neurologist',
                   available_days='Mon-Fri', available_time='10:00 AM - 4:00 PM'),
        ]
        # Create sample announcements
        announcements = [
            Announcement(
                title='Welcome to Our Hospital Management System',
                message='We are pleased to introduce our new online appointment booking system. You can now book, view, and manage your appointments online 24/7.'
            ),
            Announcement(
                title='Hospital Timings Update',
                message='Our OPD services are now available from 8:00 AM to 8:00 PM, Monday to Saturday. Emergency services are available 24/7.'
            ),
            Announcement(
                title='COVID-19 Safety Measures',
                message='Please wear masks and maintain social distancing while visiting the hospital. Temperature screening is mandatory at the entrance.'
            ),
        ]
        
        for announcement in announcements:
            db.session.add(announcement)
        
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
