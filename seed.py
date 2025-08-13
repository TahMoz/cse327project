from app import app, db
from models import Product

with app.app_context():
    db.create_all()

    if Product.query.count() == 0:
        products = [
            Product(name="Wireless Headphones", 
                    description="Comfortable over-ear wireless headphones",
                    price=2999.00, 
                    stock_quantity=50,
                    category="Electronics", 
                    image_url="/static/image/headphone.jpeg"),

            Product(name="Short Stories",
                    description="A collection of modern short stories",
                    price=399.00,
                    stock_quantity=120,
                    category="Books",
                    image_url="https://via.placeholder.com/400x300?text=Book"),

            Product(name="Men T-Shirt",
                    description="100% cotton men t-shirt",
                    price=599.00,
                    stock_quantity=80,
                    category="Clothing",
                    image_url="https://via.placeholder.com/400x300?text=T-Shirt"),

            Product(name="Bluetooth Speaker",
                    description="Portable bluetooth speaker, 10h battery", 
                    price=1299.00,
                    stock_quantity=30,
                    category="Electronics",
                    image_url="/static/image/Blutooth_speaker.jpg"),

            Product(name="Women Jeans", 
                    description="Slim fit jeans",
                    price=1599.00,
                    stock_quantity=40, 
                    category="Clothing",
                    image_url="https://via.placeholder.com/400x300?text=Jeans"),

            Product(name="Mens Jeans",
                    description="Comfortable jeans",
                    price=2000.00,
                    stock_quantity=40,
                    category="Clothing",
                    image_url="https://via.placeholder.com/400x300?text=Jeans"),

            
        ]
        db.session.add_all(products)
        db.session.commit()
        print("Seed data inserted!")
    else:
        print("Database already has data.")


    products = Product.query.all()
    for p in products:
        if p.name == "Wireless Headphones":
            p.image_url = "/static/image/Wireless_headphone.jpg"

        elif p.name == "Short Stories":
            p.image_url = "/static/image/short_story.jpg"
        
        elif p.name == "Men T-Shirt":
            p.image_url = "/static/image/Mens_tshirt.jpg"

        
        elif p.name == "Mens Jeans":
            p.image_url = "/static/image/man-jeans.jpg"

        elif p.name == "Womens Jeans":
            p.image_url = "/static/image/women_jeans.jpg"

        elif p.name == "Bkutooth Spiker":
            p.image_url = "/static/image/Blutooth_speaker.jpg"  


    db.session.commit()
    print("Image URLs updated!")
