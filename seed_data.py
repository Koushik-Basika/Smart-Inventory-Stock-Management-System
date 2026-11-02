
from decimal import Decimal

from app import app, db, User, Category, Supplier, Product, StockTransaction


# Sample categories
CATEGORIES = [
    "Electronics",
    "Computer Accessories",
    "Office Supplies",
    "Networking",
    "Storage Devices"
]


# Sample suppliers
SUPPLIERS = [
    {
        "name": "TechWorld Distributors",
        "email": "sales@techworld.example",
        "phone": "9000001001",
        "address": "Hyderabad, Telangana"
    },
    {
        "name": "Digital Hub Supplies",
        "email": "orders@digitalhub.example",
        "phone": "9000001002",
        "address": "Secunderabad, Telangana"
    },
    {
        "name": "OfficeKart Wholesale",
        "email": "support@officekart.example",
        "phone": "9000001003",
        "address": "Vijayawada, Andhra Pradesh"
    }
]


# Sample products
PRODUCTS = [
    ("Wireless Mouse", "ACC-001", "Wireless optical mouse", 35, 8, "599", "Computer Accessories", "TechWorld Distributors"),
    ("USB Keyboard", "ACC-002", "USB keyboard", 22, 6, "799", "Computer Accessories", "TechWorld Distributors"),
    ("LED Monitor", "ELE-001", "24 inch Full HD monitor", 8, 5, "8499", "Electronics", "Digital Hub Supplies"),
    ("Laptop Stand", "ACC-003", "Adjustable laptop stand", 4, 5, "1199", "Computer Accessories", "OfficeKart Wholesale"),
    ("HDMI Cable", "ACC-004", "2 metre HDMI cable", 50, 10, "249", "Computer Accessories", "TechWorld Distributors"),
    ("WiFi Router", "NET-001", "Dual band router", 6, 5, "2199", "Networking", "Digital Hub Supplies"),
    ("Ethernet Cable", "NET-002", "Cat6 network cable", 3, 10, "199", "Networking", "Digital Hub Supplies"),
    ("External Hard Drive", "STR-001", "1TB external hard drive", 12, 4, "4999", "Storage Devices", "TechWorld Distributors"),
    ("USB Drive", "STR-002", "32GB USB drive", 28, 8, "399", "Storage Devices", "TechWorld Distributors"),
    ("A4 Paper", "OFF-001", "500 sheet paper ream", 40, 10, "299", "Office Supplies", "OfficeKart Wholesale"),
    ("Wireless Headset", "ELE-002", "Bluetooth headset", 5, 5, "1799", "Electronics", "Digital Hub Supplies"),
    ("Webcam", "ELE-003", "1080p USB webcam", 0, 5, "1499", "Electronics", "Digital Hub Supplies")
]


def seed_data():

    with app.app_context():

        try:

            # Create database tables
            db.create_all()

            # 1. Create or update Admin
            admin = User.query.filter_by(
                email="koushik@gmail.com"
            ).first()

            if not admin:
                admin = User(
                    username="Koushik Reddy",
                    email="koushik@gmail.com",
                    role="admin"
                )
                db.session.add(admin)

            # Always reset Admin credentials
            admin.role = "admin"
            admin.set_password("Admin@12345")

            db.session.flush()

            # 2. Insert categories
            category_map = {}

            for name in CATEGORIES:

                category = Category.query.filter_by(
                    name=name
                ).first()

                if not category:
                    category = Category(name=name)
                    db.session.add(category)
                    db.session.flush()

                category_map[name] = category

            # 3. Insert suppliers
            supplier_map = {}

            for details in SUPPLIERS:

                supplier = Supplier.query.filter_by(
                    name=details["name"]
                ).first()

                if not supplier:
                    supplier = Supplier(**details)
                    db.session.add(supplier)
                    db.session.flush()

                supplier_map[supplier.name] = supplier

            # 4. Insert products
            for item in PRODUCTS:

                name, sku, description, quantity, reorder, price, category, supplier = item

                existing = Product.query.filter_by(
                    sku=sku
                ).first()

                if existing:
                    continue

                product = Product(
                    name=name,
                    sku=sku,
                    description=description,
                    quantity=quantity,
                    reorder_level=reorder,
                    unit_price=Decimal(price),
                    category_id=category_map[category].id,
                    supplier_id=supplier_map[supplier].id
                )

                db.session.add(product)
                db.session.flush()

                # 5. Record opening stock
                if quantity > 0:

                    transaction = StockTransaction(
                        product_id=product.id,
                        user_id=admin.id,
                        transaction_type="IN",
                        quantity=quantity,
                        note="Opening stock"
                    )

                    db.session.add(transaction)

            db.session.commit()

            print("\nSample data inserted successfully!")

            print("Users:", User.query.count())
            print("Categories:", Category.query.count())
            print("Suppliers:", Supplier.query.count())
            print("Products:", Product.query.count())
            print("Stock Transactions:", StockTransaction.query.count())

            print("\n========== ADMIN LOGIN ==========")
            print("Username: Koushik Reddy")
            print("Email: koushik@gmail.com")
            print("Password: Admin@12345")
            print("Role: admin")
            print("=================================")

        except Exception as e:

            db.session.rollback()
            print("Error inserting sample data:", e)


if __name__ == "__main__":
    seed_data()
