from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import CheckConstraint
import re
from sqlalchemy.orm import validates
import datetime

db = SQLAlchemy()

class Admin(db.Model, SerializerMixin):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    products = db.relationship('Product', back_populates='admin', lazy=True)


class Product(db.Model, SerializerMixin):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text())
    category = db.Column(db.String(64))
    sub_category = db.Column(db.String(64))
    brand = db.Column(db.String(64))
    deal_price = db.Column(db.Integer(), nullable=True, default=None)
    deal_start_time = db.Column(db.DateTime(), nullable=True, default=None)
    deal_end_time = db.Column(db.DateTime(), nullable=True, default=None)
    admin_id = db.Column(db.ForeignKey("admin.id"), nullable=False)

    cartitems = db.relationship('CartItem', back_populates='products', lazy=True)
    orderitems = db.relationship('OrderItem', back_populates='products', lazy=True)
    images= db.relationship('Image', back_populates='products', lazy=True)
    variations = db.relationship('ProductVariation', back_populates='product', lazy=True)

    def save_images(self, images):
        for image in images:
            image_data = image.read()
            new_image = Image(data=image_data)
            self.images.append(new_image)

    def add_variation(self, size, price):
        variation = ProductVariation(size=size, price=price)
        self.variations.append(variation)
        return variation
    
    def remove_variation(self, variation):
        self.variations.remove(variation)

class ProductVariation(db.Model, SerializerMixin):
    __tablename__ = "product_variations"
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(32))
    price = db.Column(db.Integer())
    product_id = db.Column(db.ForeignKey("products.id"), nullable=False)

    @validates('size')
    def validate_size(self, key, size):
        if not size:
            raise ValueError("Size cannot be empty.")
        return size
    
    @validates('price')
    def validate_price(self, key,price):
        if price is None or price < 0:
            raise ValueError("Price is required")
        return price
    


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

    orderitems = db.relationship('OrderItem', back_populates='orders', lazy=True)

class OrderItem(db.Model, SerializerMixin):
    __tablename__ = "orderitems"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer(), default=1)

    order_id = db.Column(db.ForeignKey('orders.id'))
    product_id = db.Column(db.ForeignKey('products.id'))

class Appointment(db.Model, SerializerMixin):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(128), nullable=False)
    customer_email = db.Column(db.String(128), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)


# CheckConstraint
# validations
    