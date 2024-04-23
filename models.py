from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import CheckConstraint
import re
from sqlalchemy.orm import validates

db = SQLAlchemy()

class Admin(db.Model, SerializerMixin):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    products = db.relationship('Product', backref='admin', lazy=True)

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError("Email address is required")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email format")
        return email

    @validates('password')
    def validate_password(self, key, password):
        if not password:
            raise ValueError("Password is required")
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            raise ValueError("Password must contain at least one lowercase letter, one uppercase letter, one digit, one special character, and be at least 8 characters long")
        return password


class Product(db.Model, SerializerMixin):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text())
    price = db.Column(db.Integer())
    category = db.Column(db.String(64))
    sub_category = db.Column(db.String(64))
    brand = db.Column(db.String(64))
    quantity = db.Column(db.Integer())
    admin_id = db.Column(db.ForeignKey("admin.id"), nullable=False)

    cartitems = db.relationship('CartItem', backref='products', lazy=True)
    orderitems = db.relationship('OrderItem', backref='products', lazy=True)
    images= db.relationship('Image', backref='products', lazy=True)

    def save_images(self, images):
        for image in images:
            image_data = image.read()
            new_image = Image(data=image_data)
            self.images.append(new_image)

class Image(db.Model, SerializerMixin):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.LargeBinary(length=16277215))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))

class CartItem(db.Model, SerializerMixin):
    __tablename__ = "cartitems"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer())
    session_id = db.Column(db.String(128))

    product_id = db.Column(db.ForeignKey('products.id'), nullable=False)

class Order(db.Model, SerializerMixin):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    customerFirstName = db.Column(db.String(128), nullable=False)
    customerLastName = db.Column(db.String(128), nullable=False)
    customerEmail = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(96), nullable=False)
    town = db.Column(db.String(24), nullable=False)
    phone = db.Column(db.String(30), nullable=False)

    orderitems = db.relationship('OrderItem', backref='orders', lazy=True)

class OrderItem(db.Model, SerializerMixin):
    __tablename__ = "orderitems"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer(), default=1)

    order_id = db.Column(db.ForeignKey('orders.id'))
    product_id = db.Column(db.ForeignKey('products.id'))

# CheckConstraint
# validations
    