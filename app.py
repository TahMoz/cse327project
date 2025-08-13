"""
Online Shopping App - Admin/User Login with Role-Based Access Control.

Uses Flask, SQLite, flask_jwt_extended for JWT-based authentication,
and session for lightweight cart handling.

Follows PEP 8 and is ready for Sphinx documentation.
"""

import sqlite3
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash,
)
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
    unset_jwt_cookies,
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this for production!
app.config["JWT_SECRET_KEY"] = "supersecretjwtkey"  # Change this for production!
jwt = JWTManager(app)


def get_db_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect("shopping_db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize DB: users and products tables."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
            """
        )
        # Add default admin and user if not exist
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", ("admin",))
        if cursor.fetchone() is None:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", generate_password_hash("admin123"), "admin"),
            )
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", ("user1",))
        if cursor.fetchone() is None:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("user1", generate_password_hash("user123"), "user"),
            )
        conn.commit()


@app.route("/")
def home():
    """Render homepage with login links."""
    return render_template("home.html")

@app.route("/register/admin", methods=["GET", "POST"])
def admin_register():
    """Admin registration page."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("admin_register"))

        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username already exists.", "danger")
                return redirect(url_for("admin_register"))

            hashed_password = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')",
                (username, hashed_password),
            )
            conn.commit()

        flash("Admin registered successfully. Please log in.", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin_register.html")

@app.route("/login/admin", methods=["GET", "POST"])
def admin_login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND role = 'admin'", (username,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            access_token = create_access_token(identity={"id": user["id"], "role": "admin"})
            session["access_token"] = access_token
            session["username"] = username
            session["role"] = "admin"
            flash("Admin logged in successfully.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials.", "danger")

    return render_template("admin_login.html")

@app.route("/register/user", methods=["GET", "POST"])
def user_register():
    """User registration page."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("user_register"))

        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username already exists.", "danger")
                return redirect(url_for("user_register"))

            hashed_password = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, 'user')",
                (username, hashed_password),
            )
            conn.commit()

        flash("User registered successfully. Please log in.", "success")
        return redirect(url_for("user_login"))

    return render_template("user_register.html")

@app.route("/login/user", methods=["GET", "POST"])
def user_login():
    """User login page."""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND role = 'user'", (username,)
            ).fetchone()

        if user and check_password_hash(user["password"], password):
            access_token = create_access_token(identity={"id": user["id"], "role": "user"})
            session["access_token"] = access_token
            session["username"] = username
            session["role"] = "user"
            flash("User logged in successfully.", "success")
            return redirect(url_for("user_dashboard"))

        flash("Invalid user credentials.", "danger")

    return render_template("user_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for("admin_login"))
    
    with get_db_connection() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    
    return render_template("admin_dashboard.html", username=session.get("username"), products=products)

@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        flash("Unauthorized access", "danger")
        return redirect(url_for("user_login"))
    
    with get_db_connection() as conn:
        products = conn.execute("SELECT * FROM products").fetchall()
    
    return render_template("user_dashboard.html", username=session.get("username"), products=products)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
