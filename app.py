
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# DATABASE MODELS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="seeker")


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    location = db.Column(db.String(100))
    salary = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"))


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(30), default="Pending")


# LOGIN REQUIRED DECORATOR

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") != role:
                flash("You are not authorized to access this page.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return decorated
    return decorator


# HOME PAGE

@app.route("/")
def index():
    jobs = Job.query.order_by(Job.id.desc()).limit(6).all()
    return render_template("index.html", jobs=jobs)


# REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]

        if role not in ["seeker", "employer"]:
            flash("Invalid account type.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["name"] = user.name
            session["role"] = user.role

            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# LOGOUT

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("index"))


# DASHBOARD

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    role = session["role"]

    if role == "employer":
        jobs = Job.query.filter_by(employer_id=user_id).all()
        return render_template("dashboard.html", jobs=jobs)

    if role == "admin":
        return redirect(url_for("admin"))

    applications = Application.query.filter_by(user_id=user_id).all()
    return render_template("dashboard.html", applications=applications)


# POST JOB

@app.route("/post-job", methods=["GET", "POST"])
@login_required
@role_required("employer")
def post_job():
    if request.method == "POST":
        job = Job(
            title=request.form["title"],
            company=request.form["company"],
            category=request.form["category"],
            location=request.form["location"],
            salary=request.form["salary"],
            description=request.form["description"],
            employer_id=session["user_id"]
        )

        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("post_job.html")


# EDIT JOB

@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
@login_required
@role_required("employer")
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != session["user_id"]:
        flash("You cannot edit this job.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        job.title = request.form["title"]
        job.company = request.form["company"]
        job.category = request.form["category"]
        job.location = request.form["location"]
        job.salary = request.form["salary"]
        job.description = request.form["description"]

        db.session.commit()
        flash("Job updated successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("post_job.html", job=job)


# DELETE JOB

@app.route("/delete-job/<int:job_id>", methods=["POST"])
@login_required
@role_required("employer")
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != session["user_id"]:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("dashboard"))

    Application.query.filter_by(job_id=job.id).delete()
    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully.", "success")
    return redirect(url_for("dashboard"))


# SEARCH JOBS

@app.route("/jobs")
def jobs():
    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()
    category = request.args.get("category", "").strip()
    company = request.args.get("company", "").strip()

    query = Job.query

    if keyword:
        query = query.filter(Job.title.ilike(f"%{keyword}%"))

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    if company:
        query = query.filter(Job.company.ilike(f"%{company}%"))

    all_jobs = query.order_by(Job.id.desc()).all()

    return render_template("jobs.html", jobs=all_jobs)


# JOB DETAILS

@app.route("/job/<int:job_id>")
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("job_details.html", job=job)


# APPLY FOR JOB

@app.route("/apply/<int:job_id>", methods=["POST"])
@login_required
@role_required("seeker")
def apply(job_id):
    job = Job.query.get_or_404(job_id)

    existing = Application.query.filter_by(
        job_id=job.id,
        user_id=session["user_id"]
    ).first()

    if existing:
        flash("You have already applied for this job.", "warning")
    else:
        application = Application(
            job_id=job.id,
            user_id=session["user_id"]
        )
        db.session.add(application)
        db.session.commit()
        flash("Application submitted successfully!", "success")

    return redirect(url_for("job_details", job_id=job.id))


# EMPLOYER: VIEW APPLICATIONS

@app.route("/applications/<int:job_id>")
@login_required
@role_required("employer")
def applications(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != session["user_id"]:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard"))

    records = Application.query.filter_by(job_id=job.id).all()
    applicants = [
        (application, User.query.get(application.user_id))
        for application in records
    ]

    return render_template(
        "applications.html",
        job=job,
        applicants=applicants
    )


# EMPLOYER: UPDATE APPLICATION STATUS

@app.route("/application-status/<int:application_id>", methods=["POST"])
@login_required
@role_required("employer")
def update_application(application_id):
    application = Application.query.get_or_404(application_id)
    job = Job.query.get_or_404(application.job_id)

    if job.employer_id != session["user_id"]:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard"))

    status = request.form["status"]
    if status not in ["Pending", "Shortlisted", "Rejected", "Accepted"]:
        flash("Invalid status.", "danger")
    else:
        application.status = status
        db.session.commit()
        flash("Application status updated.", "success")

    return redirect(url_for("applications", job_id=job.id))


# ADMIN DASHBOARD

@app.route("/admin")
@login_required
@role_required("admin")
def admin():
    users = User.query.all()
    jobs = Job.query.all()
    applications = Application.query.all()

    return render_template(
        "admin.html",
        users=users,
        jobs=jobs,
        applications=applications
    )


# ADMIN: DELETE USER

@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == session["user_id"]:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin"))

    if user.role == "employer":
        employer_jobs = Job.query.filter_by(employer_id=user.id).all()
        for job in employer_jobs:
            Application.query.filter_by(job_id=job.id).delete()
            db.session.delete(job)

    Application.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()

    flash("User deleted.", "success")
    return redirect(url_for("admin"))


# ADMIN: DELETE JOB

@app.route("/admin/delete-job/<int:job_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    Application.query.filter_by(job_id=job.id).delete()
    db.session.delete(job)
    db.session.commit()

    flash("Job removed.", "success")
    return redirect(url_for("admin"))


# INITIALIZE DATABASE AND ADMIN ACCOUNT

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="admin@jobportal.com").first():
        admin_user = User(
            name="Administrator",
            email="admin@jobportal.com",
            password=generate_password_hash("Admin@123"),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True)
