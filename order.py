import sqlite3
from flask import Flask, request, render_template, redirect, url_for, session
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity)

order = Flask(__name__)
order.secret_key = "supersecretkey"

order.config["JWT_SECRET_KEY"] = "supersecretjwtkey"
jwt = JWTManager(order)

def get_db_connection():
    conn = sqlite3.connect('shopping_db.sqlite')
    conn.row_factory = sqlite3.Row  
    return conn

@order.route('/products')
def product_list():
    return "Product List"

@order.route('/add_to_cart', methods=['POST'])
@jwt_required(optional=True)
def add_to_cart():
    product_id = int(request.form['product_id'])
    quantity = int(request.form.get('quantity', 1))

    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart

    return redirect(url_for('product_list'))


@order.route('/cart')
@jwt_required(optional=True)
def view_cart():
    cart = session.get('cart', {})
    products = []
    subtotal = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    for product_id, quantity in cart.items():
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if product:
            product = dict(product) 
            product['quantity'] = quantity
            product['total_price'] = product['price'] * quantity
            products.append(product)
            subtotal += product['total_price']

    conn.close()
    return render_template("cart.html", products=products, subtotal=subtotal)


@order.route('/remove_from_cart', methods=['POST'])
@jwt_required(optional=True)
def remove_from_cart():
    product_id = str(request.form['product_id'])
    cart = session.get('cart', {})

    if product_id in cart:
        del cart[product_id]

    session['cart'] = cart
    return redirect(url_for('view_cart'))

@order.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    current_user = get_jwt_identity()
    cart = session.get('cart', {})

    if not cart:
        return redirect(url_for('product_list'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO orders (user_id) VALUES (?)",
        (current_user,)
    )
    order_id = cursor.lastrowid

    for product_id, quantity in cart.items():
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
            (order_id, product_id, quantity)
        )

    conn.commit()
    conn.close()
    session['cart'] = {}

    return redirect(url_for('product_list'))

if __name__ == '__main__':
    order.run(debug=True)
