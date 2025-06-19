from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key_change_in_production"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Default password for initial setup


# Database helper functions
def get_db_connection():
    conn = sqlite3.connect("visitors.db")
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    with get_db_connection() as conn:
        # Create visits table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                purpose TEXT NOT NULL,
                check_in_time TEXT NOT NULL,
                check_out_time TEXT
            )
        """
        )

        # Create users table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                contact TEXT NOT NULL,
                address TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                role TEXT DEFAULT 'visitor'
            )
        """
        )

        # Create admin user if it doesn't exist
        admin_exists = conn.execute(
            "SELECT username FROM users WHERE username = ? AND role = 'admin'",
            (ADMIN_USERNAME,),
        ).fetchone()

        if not admin_exists:
            password_hash = hash_password(ADMIN_PASSWORD)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn.execute(
                """INSERT INTO users (username, name, contact, address, password_hash, created_at, role) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    ADMIN_USERNAME,
                    "System Administrator",
                    "admin@menarco.com",
                    "Menarco Development HQ",
                    password_hash,
                    created_at,
                    "admin",
                ),
            )
            print(
                f"Admin user created with username: {ADMIN_USERNAME} and password: {ADMIN_PASSWORD}"
            )

        conn.commit()


init_db()


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        name = request.form.get("name", "").strip()
        contact = request.form.get("contact", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not all([username, name, contact, address, password]):
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif username == ADMIN_USERNAME:
            error = "Username already taken."
        else:
            try:
                with get_db_connection() as conn:
                    # Check if username already exists
                    existing_user = conn.execute(
                        "SELECT username FROM users WHERE username = ?", (username,)
                    ).fetchone()

                    if existing_user:
                        error = "Username already taken."
                    else:
                        # Check if name already exists
                        existing_name = conn.execute(
                            "SELECT name FROM users WHERE name = ?", (name,)
                        ).fetchone()

                        if existing_name:
                            error = "Name already registered."
                        else:
                            # Insert new user
                            password_hash = hash_password(password)
                            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            conn.execute(
                                """INSERT INTO users (username, name, contact, address, password_hash, created_at) 
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (
                                    username,
                                    name,
                                    contact,
                                    address,
                                    password_hash,
                                    created_at,
                                ),
                            )
                            conn.commit()
                            flash("Registration successful! Please login.")
                            return redirect(url_for("login"))
            except sqlite3.Error as e:
                error = "Registration failed. Please try again."

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        else:
            try:
                with get_db_connection() as conn:
                    user = conn.execute(
                        "SELECT username, name, password_hash, role FROM users WHERE username = ?",
                        (username,),
                    ).fetchone()

                    if user and user["password_hash"] == hash_password(password):
                        session["username"] = username
                        session["name"] = user["name"]
                        session["role"] = user["role"]

                        if user["role"] == "admin":
                            return redirect(url_for("admin_dashboard"))
                        else:
                            return redirect(url_for("visitor_dashboard"))
                    else:
                        error = "Invalid username or password"
            except sqlite3.Error:
                error = "Login failed. Please try again."

    return render_template("login.html", error=error)


@app.route("/visitor_dashboard", methods=["GET", "POST"])
def visitor_dashboard():
    if request.method == "POST":
        visitor_name = request.form.get("visitor_name", "").strip()
        purpose = request.form.get("purpose", "").strip()
        if not visitor_name or not purpose:
            flash("Name and purpose are required for check-in.", "error")
        else:
            check_in_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO visits (username, purpose, check_in_time) VALUES (?, ?, ?)",
                        (visitor_name, purpose, check_in_time),
                    )
                    conn.commit()
                flash(f"Check-in successful at {check_in_time}", "success")
            except sqlite3.Error:
                flash("Error during check-in. Please try again.", "error")
        return redirect(url_for("visitor_dashboard"))

    # For GET, simply render the visitor form (no login check)
    return render_template("visitor_dashboard.html")


@app.route("/visitor-form")
def visitor_form():
    # Remove session check so anyone can access the form.
    return render_template("visitor_form.html")


@app.route("/visitor/profile")
def visitor_profile():
    if session.get("role") != "visitor":
        return redirect(url_for("login"))

    username = session.get("username")
    user_info = {}

    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT username, name, contact, address, created_at FROM users WHERE username = ?",
                (username,),
            ).fetchone()

            if user:
                user_info = {
                    "name": user["name"],
                    "contact": user["contact"],
                    "address": user["address"],
                    "created_at": user["created_at"],
                }
    except sqlite3.Error:
        flash("Error loading profile information.")

    return render_template(
        "visitor_profile.html", username=username, user_info=user_info
    )


@app.route("/visitor_checkout/<int:visitor_id>", methods=["POST"])
def visitor_checkout(visitor_id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    check_out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_db_connection() as conn:
            result = conn.execute(
                "UPDATE visits SET check_out_time = ? WHERE id = ?",
                (check_out_time, visitor_id),
            )
            conn.commit()

            if result.rowcount > 0:
                flash("Visitor checked out successfully.")
            else:
                flash("Visitor not found.")
    except sqlite3.Error:
        flash("Error during checkout.")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        with get_db_connection() as conn:
            visitors = conn.execute(
                "SELECT id, username, purpose, check_in_time, check_out_time FROM visits ORDER BY check_in_time DESC"
            ).fetchall()
    except sqlite3.Error:
        visitors = []
        flash("Error loading visitor data.")

    return render_template("admin_dashboard.html", visitors=visitors)


@app.route("/admin/profile")
def admin_profile():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    username = session.get("username")
    admin_info = {}

    try:
        with get_db_connection() as conn:
            admin = conn.execute(
                "SELECT username, name, contact, address, created_at FROM users WHERE username = ? AND role = 'admin'",
                (username,),
            ).fetchone()

            if admin:
                admin_info = {
                    "name": admin["name"],
                    "contact": admin["contact"],
                    "address": admin["address"],
                    "created_at": admin["created_at"],
                }
    except sqlite3.Error:
        flash("Error loading admin profile information.")

    return render_template(
        "admin_profile.html", username=username, admin_info=admin_info
    )


@app.route("/admin/visitor-log")
def admin_visitor_log():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    try:
        with get_db_connection() as conn:
            visitors = conn.execute(
                "SELECT id, username, purpose, check_in_time, check_out_time FROM visits ORDER BY check_in_time DESC"
            ).fetchall()
    except sqlite3.Error:
        visitors = []
        flash("Error loading visitor log.")

    return render_template("admin_visitor_log.html", visitors=visitors)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/")
def home():
    return render_template("home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


def calculate_duration(check_in_str, check_out_str):
    """Calculate duration between check-in and check-out times"""
    try:
        check_in = datetime.strptime(check_in_str, "%Y-%m-%d %H:%M:%S")
        check_out = datetime.strptime(check_out_str, "%Y-%m-%d %H:%M:%S")
        duration = check_out - check_in

        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60

        if duration.days > 0:
            return f"{duration.days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"


if __name__ == "__main__":
    app.run(debug=True)


# Add the function to template context
@app.context_processor
def utility_processor():
    return dict(calculate_duration=calculate_duration)


if __name__ == "__main__":
    app.run(debug=True)
