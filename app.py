import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from db import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["JWT_SECRET_KEY"] = "supersecretjwtkey"
JWTManager(app)

def require_role(role: str):
    if session.get("role") != role:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("admin_login" if role == "admin" else "user_login"))

def handle_register(role: str, template: str, success_redirect: str):
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if not u or not p:
            flash("Username and password are required.", "danger")
            return redirect(url_for(success_redirect if role == "admin" else success_redirect))
        with get_db_connection() as conn:
            if conn.execute("SELECT 1 FROM users WHERE username=?", (u,)).fetchone():
                flash("Username already exists.", "danger")
                return redirect(url_for(success_redirect))
            conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                         (u, generate_password_hash(p), role))
            conn.commit()
        flash(f"{role.capitalize()} registered. Please log in.", "success")
        return redirect(url_for("admin_login" if role == "admin" else "user_login"))
    return render_template(template)

def handle_login(role: str, template: str, dashboard_endpoint: str):
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username=? AND role=?", (u, role)
            ).fetchone()
        if user and check_password_hash(user["password"], p):
            token = create_access_token(identity={"id": user["id"], "role": role})
            session.update({"access_token": token, "username": u, "role": role, "user_id": user["id"]})
            flash(f"Logged in as {role}.", "success")
            return redirect(url_for(dashboard_endpoint))
        flash(f"Invalid {role} credentials.", "danger")
    return render_template(template)

def dashboard_query(is_admin: bool):
    with get_db_connection() as conn:
        if is_admin:
            return conn.execute(
                "SELECT id, name, description, price, is_active FROM products ORDER BY id DESC"
            ).fetchall()
        return conn.execute(
            "SELECT id, name, description, price FROM products WHERE is_active=1 ORDER BY id DESC"
        ).fetchall()

@app.route("/")
def home(): return render_template("home.html")

@app.route("/register/admin", methods=["GET", "POST"])
def admin_register(): return handle_register("admin", "admin_register.html", "admin_register")

@app.route("/login/admin", methods=["GET", "POST"])
def admin_login(): return handle_login("admin", "admin_login.html", "admin_dashboard")

@app.route("/register/user", methods=["GET", "POST"])
def user_register(): return handle_register("user", "user_register.html", "user_register")

@app.route("/login/user", methods=["GET", "POST"])
def user_login(): return handle_login("user", "user_login.html", "user_dashboard")

@app.route("/logout")
def logout():
    session.clear(); flash("Logged out.", "success"); return redirect(url_for("home"))

@app.route("/admin/dashboard")
def admin_dashboard():
    r = require_role("admin")
    if r: return r
    products = dashboard_query(is_admin=True)
    return render_template("admin_dashboard.html", username=session.get("username"), products=products)

@app.route("/user/dashboard")
def user_dashboard():
    r = require_role("user")
    if r: return r
    products = dashboard_query(is_admin=False)
    return render_template("user_dashboard.html", username=session.get("username"), products=products)

@app.route("/products")
def product_list():
    with get_db_connection() as conn:
        try:
            rows = conn.execute(
                "SELECT id, name, price FROM products WHERE is_active=1 ORDER BY id DESC"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = conn.execute("SELECT id, name, price FROM products ORDER BY id DESC").fetchall()
    return render_template("product_list.html", products=rows)

@app.route("/my_orders")
def my_orders():
    r = require_role("user")
    if r: return r
    uid = session.get("user_id")
    with get_db_connection() as conn:
        orders = conn.execute(
            """
            SELECT o.id, o.created_at, o.total_price, o.address, o.payment_method,
                   COALESCE(SUM(oi.quantity), 0) AS item_count
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id = ?
            GROUP BY o.id
            ORDER BY o.created_at DESC
            """,
            (uid,),
        ).fetchall()
    return render_template("my_orders.html", orders=orders)

@app.route("/orders/<int:order_id>")
def order_detail(order_id: int):
    r = require_role("user")
    if r: return r
    uid = session.get("user_id")
    with get_db_connection() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order or order["user_id"] != uid:
            flash("Order not found.", "danger"); return redirect(url_for("my_orders"))
        items = conn.execute(
            """
            SELECT oi.product_id, p.name AS product_name, oi.quantity, oi.price,
                   (oi.quantity * oi.price) AS subtotal
            FROM order_items oi JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        ).fetchall()
    return render_template("order_detail.html", order=order, items=items)

@app.route("/admin/products")
def admin_products():
    r = require_role("admin")
    if r: return r
    q = request.args.get("q", "").strip()
    sql = "SELECT id, name, description, price, is_active FROM products"
    params = []
    if q: sql += " WHERE name LIKE ?"; params.append(f"%{q}%")
    sql += " ORDER BY id DESC"
    with get_db_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return render_template("admin_products.html", products=rows, q=q)

@app.route("/admin/products/new", methods=["GET", "POST"])
def add_product():
    r = require_role("admin")
    if r: return r
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        is_active = 1 if request.form.get("is_active") == "on" else 0
        if not name or not price:
            flash("Name and price are required.", "danger"); return redirect(url_for("add_product"))
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO products (name, description, price, is_active) VALUES (?,?,?,?)",
                (name, description, float(price), is_active),
            ); conn.commit()
        flash("Product created.", "success"); return redirect(url_for("admin_products"))
    return render_template("admin_product_form.html", mode="create")

@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id: int):
    r = require_role("admin")
    if r: return r
    with get_db_connection() as conn:
        product = conn.execute(
            "SELECT id, name, description, price, is_active FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not product:
            flash("Product not found.", "danger"); return redirect(url_for("admin_products"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        is_active = 1 if request.form.get("is_active") == "on" else 0
        if not name or not price:
            flash("Name and price are required.", "danger")
            return redirect(url_for("edit_product", product_id=product_id))
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE products SET name=?, description=?, price=?, is_active=? WHERE id=?",
                (name, description, float(price), is_active, product_id),
            ); conn.commit()
        flash("Product updated.", "success"); return redirect(url_for("admin_products"))
    return render_template("admin_product_form.html", mode="edit", product=product)

@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id: int):
    r = require_role("admin")
    if r: return r
    with get_db_connection() as conn:
        conn.execute("UPDATE products SET is_active=0 WHERE id=?", (product_id,)); conn.commit()
    flash("Product deleted (soft).", "success"); return redirect(url_for("admin_products"))

if __name__ == "__main__":
    init_db(); app.run(debug=True)
