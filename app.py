from flask import Flask, render_template, request, jsonify
from config import Config
from models import db, Product
from sqlalchemy import or_, desc, asc

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    db.init_app(app)
    return app

app = create_app()

@app.route("/")
def index():
    return render_template("products.html")

@app.route("/api/products")
def api_products():
    q = request.args.get("q", type=str, default="").strip()
    category = request.args.get("category", type=str)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", default="newest")
    page = request.args.get("page", type=int, default=1)
    per_page = request.args.get("per_page", type=int, default=12)

    query = Product.query

    if q:
        like_pattern = f"%{q}%"
        query = query.filter(or_(
            Product.name.ilike(like_pattern),
            Product.description.ilike(like_pattern)
        ))

    if category:
        query = query.filter(Product.category == category)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(asc(Product.price))
    elif sort == "price_desc":
        query = query.order_by(desc(Product.price))
    else:
        query = query.order_by(desc(Product.created_at))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [p.to_dict() for p in pagination.items]

    return jsonify({
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "items": items
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
