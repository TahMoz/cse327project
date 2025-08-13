import sqlite3
from werkzeug.security import generate_password_hash

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect("shopping_db.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

def _column_exists(conn: sqlite3.Connection, table: str, col: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == col for r in rows)

def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','user'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)
        if not _column_exists(conn, "products", "is_active"):
            conn.execute("ALTER TABLE products ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_price REAL DEFAULT 0,
                address TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'paid',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        """)
        if not conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
            conn.execute(
                "INSERT INTO users (username,password,role) VALUES (?,?, 'admin')",
                ("admin", generate_password_hash("admin123")),
            )
        if not conn.execute("SELECT 1 FROM users WHERE username='user1'").fetchone():
            conn.execute(
                "INSERT INTO users (username,password,role) VALUES (?,?, 'user')",
                ("user1", generate_password_hash("user123")),
            )
        conn.commit()
