# Job Portal Web Application

A Flask-based job portal for job seekers, employers, and administrators. Users can browse and search job listings, employers can manage openings and applications, and administrators can manage users and jobs.

## Features

- Account registration and login for job seekers and employers
- Job search by keyword, location, category, and company
- Employer job posting, editing, and deletion
- Job applications with employer-managed application statuses
- Administrator dashboard for managing users and listings
- SQLite database initialized automatically on startup

## Requirements

- Python 3.9 or later
- pip

## Run locally

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   On Windows:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   On macOS or Linux:

   ```bash
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the application:

   ```bash
   python app.py
   ```

4. Visit <http://127.0.0.1:5000>.

The app creates its SQLite database in Flask's `instance` directory when it starts.

## Demo administrator account

The application creates this administrator account if it does not already exist:

- Email: `admin@jobportal.com`
- Password: `Admin@123`

Change or remove these demo credentials before exposing the application to other users. For deployment, also replace the development secret key in `app.py` with a securely generated value, disable Flask debug mode, and configure production hosting.
