from flask import Blueprint, render_template, request, redirect, url_for
from database import get_db

product_reviews_bp = Blueprint('product_reviews', __name__)

@product_reviews_bp.route('/product/<int:product_id>', methods=['GET','POST'])
def product_reviews(product_id):
    db = get_db()
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        user_id = 2  # Dummy user
        existing = db.execute(
            'SELECT * FROM reviews WHERE product_id=? AND user_id=?',
            (product_id, user_id)
        ).fetchone()
        if existing:
            db.execute(
                'UPDATE reviews SET rating=?, comment=? WHERE id=?',
                (rating, comment, existing['id'])
            )
        else:
            db.execute(
                'INSERT INTO reviews (product_id, user_id, rating, comment) '
                'VALUES (?, ?, ?, ?)',
                (product_id, user_id, rating, comment)
            )
        db.commit()
        return redirect(url_for('product_reviews.product_reviews', product_id=product_id))

    product = db.execute('SELECT * FROM products WHERE id=?', (product_id,)).fetchone()
    reviews = db.execute(
        'SELECT reviews.rating, reviews.comment, users.username '
        'FROM reviews JOIN users ON reviews.user_id = users.id '
        'WHERE reviews.product_id=?', (product_id,)
    ).fetchall()
    avg_rating = db.execute(
        'SELECT AVG(rating) as avg_rating FROM reviews WHERE product_id=?', (product_id,)
    ).fetchone()['avg_rating']

    return render_template(
        'product_reviews.html',
        product=product,
        reviews=reviews,
        avg_rating=avg_rating or 0
    )
