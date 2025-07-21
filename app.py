"""
Main Flask application for Online Bookstore.

Author: Aleya Akter
"""

from flask import Flask, session, redirect, url_for, request, render_template

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session

# Sample product list (normally fetched from a DB)
products = {
    1: {"title": "Python for Beginners", "price": 25},
    2: {"title": "Flask Essentials", "price": 40},
}

@app.route('/')
def product_list():
    return render_template('products.html', products=products)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    return render_template('cart.html', cart=cart, products=products)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        session.pop('cart', None)  # Clear cart after checkout
        return f"Thank you {name}, your order has been placed!"
    return render_template('checkout.html')

# This MUST be at the bottom
if __name__ == '__main__':
    app.run(debug=True)
