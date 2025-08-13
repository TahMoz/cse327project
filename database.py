import sqlite3

DB_NAME = 'stepnwear.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    cur = db.cursor()

    # Users
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT
        )
    ''')

    # Products
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    ''')

    # Orders
    cur.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            status TEXT
        )
    ''')

    # Order items
    cur.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER
        )
    ''')

    # Reviews
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT
        )
    ''')

    # Add dummy data if empty
    if not cur.execute("SELECT * FROM users").fetchone():
        cur.execute("INSERT INTO users (username, role) VALUES ('admin', 'admin')")
        cur.execute("INSERT INTO users (username, role) VALUES ('user1', 'user')")

    if not cur.execute("SELECT * FROM products").fetchone():
        cur.execute("INSERT INTO products (name, price) VALUES ('Sneaker A', 50)")
        cur.execute("INSERT INTO products (name, price) VALUES ('Sneaker B', 70)")

    if not cur.execute("SELECT * FROM orders").fetchone():
        cur.execute("INSERT INTO orders (user_id, status) VALUES (2, 'Pending')")
        cur.execute("INSERT INTO order_items (order_id, product_id) VALUES (1, 1)")

    db.commit()
    db.close()
