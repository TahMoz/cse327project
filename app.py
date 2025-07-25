from flask import Flask, render_template, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"

products = {
    "1": {"title": "Book A", "price": 10},
    "2": {"title": "Book B", "price": 15},
    "3": {"title": "Book C", "price": 20},
}

@app.route('/')
def product_list():
    return render_template('products.html', products=products)

@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    if product_id not in products:
        return "Product not found", 404

    cart = session.get('cart', {})  # get existing cart or empty dict
    
    # Only add/update clicked product
    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1
    
    session['cart'] = cart
    session.modified = True

    return redirect(url_for('product_list'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})  # get current cart
    
    cart_items = []
    total = 0

    # Only loop over products in cart — no extra products!
    for product_id, quantity in cart.items():
        if quantity > 0 and product_id in products:
            product = products[product_id]
            subtotal = product['price'] * quantity
            total += subtotal
            cart_items.append({
                'id': product_id,
                'title': product['title'],
                'price': product['price'],
                'quantity': quantity,
                'subtotal': subtotal,
            })

    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if product_id in cart:
        if cart[product_id] > 1:
            cart[product_id] -= 1  # Decrease quantity by 1
        else:
            cart.pop(product_id)  # Remove item completely if quantity is 1
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/confirm_order')
def confirm_order():
    session.pop('cart', None)  # optional: clear cart
    return render_template('confirm_order.html')


if __name__ == '__main__':
    app.run(debug=True)
