from flask import Flask, render_template
from database import init_db
from admin_orders import admin_orders_bp
from product_reviews import product_reviews_bp

app = Flask(__name__)
app.secret_key = 'secret'

# Register blueprints
app.register_blueprint(admin_orders_bp)
app.register_blueprint(product_reviews_bp)

@app.route('/')
def index():
    return """
    <h1 style='color:#2c3e50;'>Welcome to StepNwear</h1>
    <p>Use the links below to explore:</p>
    <ul>
    <li><a href='/admin/orders'>Admin: View All Orders</a></li>
    <li><a href='/product/1'>Product Reviews</a></li>
    </ul>
    """

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
