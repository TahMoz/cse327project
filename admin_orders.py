from flask import Blueprint, render_template
from database import get_db

admin_orders_bp = Blueprint('admin_orders', __name__)

@admin_orders_bp.route('/admin/orders')
def view_orders():
    db = get_db()
    orders = db.execute(
        'SELECT orders.id, orders.status, users.username '
        'FROM orders JOIN users ON orders.user_id = users.id'
    ).fetchall()

    order_details = {}
    for order in orders:
        items = db.execute(
            'SELECT products.name FROM order_items '
            'JOIN products ON order_items.product_id = products.id '
            'WHERE order_items.order_id = ?', (order['id'],)
        ).fetchall()
        order_details[order['id']] = [item['name'] for item in items]

    return render_template('admin_orders.html', orders=orders, order_details=order_details)
