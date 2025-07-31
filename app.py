"""Flask app for shopping store - Add to Cart and Place Order.

This app allows users to browse products, manage a cart, and place orders.
It uses JWT for authentication, session for temporary storage, and MySQL for data.
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flasgger import Swagger
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# JWT and Swagger configuration
app.config['JWT_SECRET_KEY'] = 'your-jwt-secret'
jwt = JWTManager(app)
swagger = Swagger(app)

# Global MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="shopping_db"
)
cursor = db.cursor()

@app.route('/')
@jwt_required(optional=True)
def product_list():
    """
    Display a list of available products.

    ---
    responses:
      200:
        description: List of products
    """
    cursor.execute("SELECT id, name, price FROM products")
    products = cursor.fetchall()
    return render_template('product_list.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
@jwt_required(optional=True)
def add_to_cart():
    """
    Add a product to the cart.

    ---
    parameters:
      - name: product_id
        in: formData
        type: integer
        required: true
      - name: quantity
        in: formData
        type: integer
        default: 1
    responses:
      302:
        description: Redirect to product list
    """
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    if 'cart' not in session:
        session['cart'] = []

    for item in session['cart']:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            break
    else:
        session['cart'].append({'product_id': product_id, 'quantity': quantity})

    session.modified = True
    return redirect(url_for('product_list'))

@app.route('/cart')
@jwt_required(optional=True)
def view_cart():
    """
    View the current shopping cart and subtotal.

    ---
    responses:
      200:
        description: Cart details
    """
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', cart=[], total=0)

    cart = session['cart']
    product_ids = [item['product_id'] for item in cart]

    format_strings = ','.join(['%s'] * len(product_ids))
    query = f"SELECT id, name, price FROM products WHERE id IN ({format_strings})"
    cursor.execute(query, tuple(product_ids))
    products = cursor.fetchall()

    cart_details = []
    total = 0
    for item in cart:
        for prod in products:
            if int(item['product_id']) == prod[0]:
                subtotal = prod[2] * item['quantity']
                total += subtotal
                cart_details.append({
                    'id': prod[0],
                    'name': prod[1],
                    'price': prod[2],
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })

    return render_template('cart.html', cart=cart_details, total=total)

@app.route('/remove_from_cart', methods=['POST'])
@jwt_required(optional=True)
def remove_from_cart():
    """
    Remove or decrement a product from the cart.

    ---
    parameters:
      - name: product_id
        in: formData
        type: integer
        required: true
    responses:
      302:
        description: Redirect to view_cart
    """
    product_id = request.form.get('product_id')
    if 'cart' in session:
        for item in session['cart']:
            if item['product_id'] == product_id:
                item['quantity'] -= 1
                if item['quantity'] <= 0:
                    session['cart'].remove(item)
                break
        session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@jwt_required(optional=True)
def checkout():
    """
    Enter shipping address and payment method.

    ---
    responses:
      200:
        description: Render checkout form or redirect to review order
    """
    if request.method == 'POST':
        address = request.form['address']
        payment_method = request.form['payment_method']
        session['checkout_info'] = {
            'address': address,
            'payment_method': payment_method
        }
        return redirect(url_for('review_order'))

    return render_template('checkout.html')

@app.route('/review_order')
@jwt_required(optional=True)
def review_order():
    """
    Review the order before placing.

    ---
    responses:
      200:
        description: Render order summary page
    """
    cart = session.get('cart', [])
    checkout_info = session.get('checkout_info')

    if not cart or not checkout_info:
        return redirect(url_for('view_cart'))

    product_ids = [item['product_id'] for item in cart]
    format_strings = ','.join(['%s'] * len(product_ids))
    cursor.execute(
        f"SELECT id, name, price FROM products WHERE id IN ({format_strings})",
        tuple(product_ids)
    )
    products = cursor.fetchall()

    cart_details = []
    total = 0

    for item in cart:
        for prod in products:
            if int(item['product_id']) == prod[0]:
                subtotal = prod[2] * item['quantity']
                total += subtotal
                cart_details.append({
                    'id': prod[0],
                    'name': prod[1],
                    'price': prod[2],
                    'quantity': item['quantity'],
                    'subtotal': subtotal
                })

    return render_template(
        'review_order.html',
        cart=cart_details,
        total=total,
        address=checkout_info['address'],
        payment_method=checkout_info['payment_method']
    )

@app.route('/place_order', methods=['POST'])
@jwt_required()
def place_order():
    """
    Finalize the order and save it to the database.

    ---
    responses:
      200:
        description: Order placed successfully
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    address = request.form.get('address')
    payment_method = request.form.get('payment_method')

    if not address or not payment_method:
        return "Address and payment method are required", 400

    if 'cart' not in session or not session['cart']:
        return "Cart is empty", 400

    cart = session['cart']
    product_ids = [item['product_id'] for item in cart]

    format_strings = ','.join(['%s'] * len(product_ids))
    cursor.execute(f"SELECT id, price FROM products WHERE id IN ({format_strings})", tuple(product_ids))
    products = cursor.fetchall()
    price_map = {prod[0]: prod[1] for prod in products}

    total_price = sum(price_map[int(item['product_id'])] * item['quantity'] for item in cart)

    cursor.execute(
        "INSERT INTO orders (user_id, total_price, address, payment_method) VALUES (%s, %s, %s, %s)",
        (user_id, total_price, address, payment_method)
    )
    order_id = cursor.lastrowid

    for item in cart:
        prod_id = int(item['product_id'])
        quantity = item['quantity']
        price = price_map.get(prod_id, 0)
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, prod_id, quantity, price)
        )

    db.commit()
    session.pop('cart', None)
    return render_template("order_success.html", order_id=order_id)

@app.route('/confirm_order', methods=['POST'])
@jwt_required(optional=True)
def confirm_order():
    """
    Confirm and finalize order using session data.

    ---
    responses:
      200:
        description: Order confirmed
    """
    user_id = get_jwt_identity()
    cart = session.get('cart', [])
    checkout_info = session.get('checkout_info')

    if not cart or not checkout_info:
        return redirect(url_for('product_list'))

    address = checkout_info['address']
    payment_method = checkout_info['payment_method']

    total_price = 0
    for item in cart:
        cursor.execute("SELECT price FROM products WHERE id = %s", (item['product_id'],))
        price = cursor.fetchone()[0]
        total_price += price * item['quantity']

    cursor.execute(
        "INSERT INTO orders (user_id, total_price, address, payment_method) VALUES (%s, %s, %s, %s)",
        (user_id, total_price, address, payment_method)
    )
    order_id = cursor.lastrowid

    for item in cart:
        cursor.execute("SELECT price FROM products WHERE id = %s", (item['product_id'],))
        price = cursor.fetchone()[0]
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
            (order_id, item['product_id'], item['quantity'], price)
        )

    db.commit()
    session.pop('cart', None)
    session.pop('checkout_info', None)

    return render_template('order_confirm.html')

if __name__ == "__main__":
    app.run(debug=True)
