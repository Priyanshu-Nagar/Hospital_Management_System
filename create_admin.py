from app import app
from models import db, User

def create_admin():
    """Create admin user manually"""
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@hospital.com').first()
        
        if existing_admin:
            print("⚠️  Admin already exists!")
            print(f"Email: {existing_admin.email}")
            print("Role: admin")
            print("\nIf you forgot the password, delete the user and run this script again.")
            return
        
        # Create new admin
        admin = User(
            name='Admin',
            email='admin@hospital.com',
            role='admin'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 50)
        print("✅ Admin created successfully!")
        print("=" * 50)
        print("Email: admin@hospital.com")
        print("Password: admin123")
        print("=" * 50)
        print("\nYou can now login at: http://127.0.0.1:5000/auth/login")

if __name__ == '__main__':
    create_admin()