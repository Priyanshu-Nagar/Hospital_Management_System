# Hospital Management System - Setup Instructions

## Step 1: Create Virtual Environment

### For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### For macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 3: Initialize Database
```bash
python init_db.py
```

## Step 4: Run the Flask Application

### For Windows:
```bash
set FLASK_APP=app.py
set FLASK_ENV=development
flask run
```

### For macOS/Linux:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Alternative (Works on all platforms):
```bash
python app.py
```

## Step 5: Access the Application
Open your browser and go to:
```
http://127.0.0.1:5000
```

## Default Admin Credentials
After running `init_db.py`, use these credentials to login as admin:
```
Email: admin@hospital.com
Password: admin123
```

## Deactivate Virtual Environment (when done)
```bash
deactivate
```

---

## Quick Start Commands (Summary)

```bash
# 1. Create and activate virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 2. Install packages
pip install -r requirements.txt

# 3. Initialize database
python init_db.py

# 4. Run application
python app.py
```

---

## Troubleshooting

### Port already in use:
```bash
# Run on different port
flask run --port 5001
```

### Database errors:
```bash
# Delete existing database and recreate
# Windows: del instance\hospital.db
# Mac/Linux: rm instance/hospital.db
python init_db.py
```
