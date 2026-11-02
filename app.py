
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost/inventory_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

csrf = CSRFProtect(app)


# ================= USER MODEL =================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ================= CATEGORY MODEL =================

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    products = db.relationship("Product", backref="category", lazy=True)


# ================= SUPPLIER MODEL =================

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)

    products = db.relationship("Product", backref="supplier", lazy=True)


# ================= PRODUCT MODEL =================

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=5)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", ondelete="SET NULL")
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier.id", ondelete="SET NULL")
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= STOCK TRANSACTION MODEL =================

class StockTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    transaction_type = db.Column(db.String(3), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product")
    user = db.relationship("User")


# ================= LOGIN MANAGER =================

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ================= ADMIN DECORATOR =================

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):

        if not current_user.is_authenticated:
            return login_manager.unauthorized()

        if current_user.role.lower() != "admin":
            abort(403)

        return view(*args, **kwargs)

    return wrapped


# ================= HOME =================

@app.route("/")
def home():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:

            flash(
                "Enter all fields. Password must contain at least 8 characters.",
                "danger"
            )

        elif User.query.filter(
            or_(
                func.lower(User.username) == username.lower(),
                func.lower(User.email) == email
            )
        ).first():

            flash("Username or email already exists.", "danger")

        else:

            user = User(
                username=username,
                email=email,
                role="staff"
            )

            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash("Account created. You can now sign in.", "success")

            return redirect(url_for("login"))

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")

        if not identity or not password:

            flash("Enter username/email and password.", "danger")

            return render_template("login.html")

        normalized_identity = identity.casefold()

        user = User.query.filter(
            or_(
                func.lower(User.email) == normalized_identity,
                func.lower(User.username) == normalized_identity
            )
        ).first()

        if user and user.check_password(password):

            login_user(user)

            flash(
                f"Welcome, {user.username}!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid username/email or password.",
            "danger"
        )

    return render_template("login.html")


# ================= LOGOUT =================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# ================= DASHBOARD =================

@app.route("/dashboard")
@login_required
def dashboard():

    total_products = Product.query.count()

    total_units = db.session.query(
        func.coalesce(func.sum(Product.quantity), 0)
    ).scalar()

    stock_value = db.session.query(
        func.coalesce(
            func.sum(Product.quantity * Product.unit_price), 0
        )
    ).scalar()

    low_stock = Product.query.filter(
        Product.quantity <= Product.reorder_level
    ).order_by(Product.quantity.asc()).limit(8).all()

    recent = StockTransaction.query.order_by(
        StockTransaction.created_at.desc()
    ).limit(8).all()

    chart_products = Product.query.order_by(
        Product.quantity.asc()
    ).limit(6).all()

    labels = [p.name for p in chart_products]
    values = [p.quantity for p in chart_products]

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_units=total_units,
        stock_value=stock_value,
        low_stock=low_stock,
        recent=recent,
        chart_labels=labels,
        chart_values=values
    )


# ================= PRODUCTS =================

@app.route("/products")
@login_required
def products():

    term = request.args.get("q", "").strip()

    query = Product.query

    if term:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{term}%"),
                Product.sku.ilike(f"%{term}%")
            )
        )

    items = query.order_by(Product.name).all()

    return render_template(
        "products.html",
        products=items,
        search=term
    )


# ================= ADD PRODUCT =================

@app.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():

    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()

    if request.method == "POST":

        try:

            name = request.form["name"].strip()
            sku = request.form["sku"].strip().upper()

            quantity = int(request.form.get("quantity", 0))
            reorder = int(request.form.get("reorder_level", 5))
            price = Decimal(request.form.get("unit_price", "0"))

            if not name or not sku or quantity < 0 or reorder < 0 or price < 0:
                raise ValueError()

            if Product.query.filter_by(sku=sku).first():

                flash("SKU already exists.", "danger")

            else:

                product = Product(
                    name=name,
                    sku=sku,
                    description=request.form.get("description"),
                    quantity=quantity,
                    reorder_level=reorder,
                    unit_price=price,
                    category_id=request.form.get("category_id") or None,
                    supplier_id=request.form.get("supplier_id") or None
                )

                db.session.add(product)
                db.session.flush()

                if quantity:

                    transaction = StockTransaction(
                        product_id=product.id,
                        user_id=current_user.id,
                        transaction_type="IN",
                        quantity=quantity,
                        note="Opening stock"
                    )

                    db.session.add(transaction)

                db.session.commit()

                flash("Product added successfully.", "success")

                return redirect(url_for("products"))

        except (ValueError, InvalidOperation, KeyError):

            db.session.rollback()

            flash(
                "Enter valid product details. Quantities and price cannot be negative.",
                "danger"
            )

    return render_template(
        "product_form.html",
        product=None,
        categories=categories,
        suppliers=suppliers
    )


# ================= EDIT PRODUCT =================

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):

    product = Product.query.get_or_404(product_id)

    categories = Category.query.order_by(Category.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()

    if request.method == "POST":

        try:

            product.name = request.form["name"].strip()
            product.sku = request.form["sku"].strip().upper()

            product.reorder_level = int(
                request.form.get("reorder_level", 5)
            )

            product.unit_price = Decimal(
                request.form.get("unit_price", "0")
            )

            product.description = request.form.get("description")

            product.category_id = request.form.get("category_id") or None
            product.supplier_id = request.form.get("supplier_id") or None

            duplicate = Product.query.filter(
                Product.sku == product.sku,
                Product.id != product.id
            ).first()

            if (
                duplicate
                or product.reorder_level < 0
                or product.unit_price < 0
            ):
                raise ValueError()

            db.session.commit()

            flash("Product updated successfully.", "success")

            return redirect(url_for("products"))

        except (ValueError, InvalidOperation, KeyError):

            db.session.rollback()

            flash("Invalid details or duplicate SKU.", "danger")

    return render_template(
        "product_form.html",
        product=product,
        categories=categories,
        suppliers=suppliers
    )


# ================= DELETE PRODUCT =================

@app.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)

    if StockTransaction.query.filter_by(
        product_id=product.id
    ).first():

        flash(
            "This product has stock history and cannot be deleted.",
            "warning"
        )

    else:

        db.session.delete(product)
        db.session.commit()

        flash("Product deleted successfully.", "success")

    return redirect(url_for("products"))


# ================= CATEGORIES =================

@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if name and not Category.query.filter_by(name=name).first():

            db.session.add(Category(name=name))
            db.session.commit()

            flash("Category added successfully.", "success")

        else:

            flash("Enter a new category name.", "warning")

        return redirect(url_for("categories"))

    return render_template(
        "categories.html",
        categories=Category.query.order_by(Category.name).all()
    )


# ================= SUPPLIERS =================

@app.route("/suppliers", methods=["GET", "POST"])
@login_required
def suppliers():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        if name:

            supplier = Supplier(
                name=name,
                email=request.form.get("email"),
                phone=request.form.get("phone"),
                address=request.form.get("address")
            )

            db.session.add(supplier)
            db.session.commit()

            flash("Supplier added successfully.", "success")

        else:

            flash("Supplier name is required.", "danger")

        return redirect(url_for("suppliers"))

    return render_template(
        "suppliers.html",
        suppliers=Supplier.query.order_by(Supplier.name).all()
    )


# ================= STOCK MANAGEMENT =================

@app.route("/stock", methods=["GET", "POST"])
@login_required
def stock():

    products_list = Product.query.order_by(Product.name).all()

    if request.method == "POST":

        try:

            product = Product.query.get_or_404(
                int(request.form["product_id"])
            )

            kind = request.form["transaction_type"]
            quantity = int(request.form["quantity"])

            if kind not in ("IN", "OUT") or quantity <= 0:
                raise ValueError()

            if kind == "OUT" and quantity > product.quantity:

                flash(
                    f"Insufficient stock. Available quantity: {product.quantity}.",
                    "danger"
                )

            else:

                if kind == "IN":
                    product.quantity += quantity
                else:
                    product.quantity -= quantity

                transaction = StockTransaction(
                    product_id=product.id,
                    user_id=current_user.id,
                    transaction_type=kind,
                    quantity=quantity,
                    note=request.form.get("note", "").strip()
                )

                db.session.add(transaction)
                db.session.commit()

                flash("Stock transaction recorded.", "success")

                return redirect(url_for("stock"))

        except (ValueError, KeyError):

            db.session.rollback()

            flash(
                "Select a product and enter a valid positive quantity.",
                "danger"
            )

    history = StockTransaction.query.order_by(
        StockTransaction.created_at.desc()
    ).limit(100).all()

    return render_template(
        "stock.html",
        products=products_list,
        transactions=history
    )


# ================= REPORTS =================

@app.route("/reports")
@login_required
def reports():

    transactions = StockTransaction.query.order_by(
        StockTransaction.created_at.desc()
    ).all()

    products_list = Product.query.order_by(Product.name).all()

    return render_template(
        "reports.html",
        transactions=transactions,
        products=products_list
    )


# ================= REST API =================

@app.route("/api/products")
@login_required
def api_products():

    rows = Product.query.order_by(Product.name).all()

    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "quantity": p.quantity,
            "reorder_level": p.reorder_level,
            "unit_price": float(p.unit_price)
        }
        for p in rows
    ])


# ================= ERROR HANDLERS =================

@app.errorhandler(403)
def forbidden(error):

    return render_template(
        "error.html",
        code=403,
        message="You do not have permission to access this page."
    ), 403


@app.errorhandler(404)
def not_found(error):

    return render_template(
        "error.html",
        code=404,
        message="The requested page was not found."
    ), 404


# ================= RUN APPLICATION =================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)
