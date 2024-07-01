from flask import request, jsonify, make_response, session
from flask_restx import Resource, Namespace
from flask_mail import Message
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token
from jwt.exceptions import DecodeError
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from models import Admin, db, Product, Image, CartItem, Appointment, Order, OrderItem, ProductVariation, CustomerEmails, DiscountCode
from datetime import datetime, timezone, timedelta
import json
import secrets
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import logging
import time
import requests
from requests.auth import HTTPBasicAuth
import base64
import re
import hashlib
import hmac
from dotenv import load_dotenv
import logging

from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction

logger = logging.getLogger(__name__)

ns = Namespace("vitapharm", description="CRUD endpoints")
bcrypt = Bcrypt()
load_dotenv()


PAYSTACK_SECRET_KEY = 'sk_test_bb4c6c67d587b34d9c23994bdbeb202d2715b3b7'

#darajaAPI
def getAccessToken():
    consumer_key = "xyyfojxRcUqE57AMT1qAlc6WLKSXZGGzwUReLA2uCQAbmqaN"
    consumer_secret = "cl8uGswLYcvNAEQZDQxLBfadKxJXp8oMANWy4P8OTqdcT7V8vpDjckWyDxzAYwgZ"
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    my_access_token = r.json()['access_token']
    return my_access_token

# Generates JWT token for session
def generate_session_token():
    random_identity = secrets.token_urlsafe(16)
    access_expires = timedelta(hours=1)
    refresh_expires = timedelta(days=30)
    access_token = create_access_token(identity=random_identity, expires_delta=access_expires)
    refresh_token = create_refresh_token(identity=random_identity, expires_delta=refresh_expires)
    return access_token, refresh_token

# Extracts session identity
def get_session_identity():
    return get_jwt_identity()


def verify_paystack_signature(request):
    signature = request.headers.get('x-paystack-signature')
    if not signature:
        return False

    payload = request.get_data()
    generated_signature = hmac.new(
        PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(generated_signature, signature)

# JWT session-management
@ns.route("/session")
class Session(Resource):
    def get(self):
        # Generate session token for the current session
        session_token, refresh_token = generate_session_token()
        # Stores the session token in Flask session
        session['session_token'] = session_token
        return make_response(jsonify({"session_token": session_token, "refresh_token": refresh_token}), 200)
    
@ns.route("/session/refresh")
class RefreshSession(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user)
        return make_response(jsonify({"session_token": new_token}), 200)

@ns.route("/home")
class Hello(Resource):
    def get(self):
        return "Welcome to the first route"


@ns.route("/signup")
class AdminSignup(Resource):
    def post(self):
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return make_response(jsonify("Invalid email or password"), 400)
            
            # quesy if admin exists
            existing_user = Admin.query.filter_by(email=email).first()
            if existing_user:
                return make_response(jsonify({"error": "User with this email already exists"}), 409)
            
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            new_user = Admin(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            return make_response(jsonify({"message": "user created"}))
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
@ns.route("/customeremails")
class CustomerEmailsResource(Resource):
    def get(self):
        try:
            # Query all customer emails from the database
            customer_emails = CustomerEmails.query.all()

            # Serialize customer emails using SerializerMixin
            serialized_emails = [email.to_dict() for email in customer_emails]

            # Return JSON response
            return jsonify(serialized_emails), 200

        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 500)
    def post(self):
        try:
            data = request.get_json()
            email = data.get('email')

            # Validate email format
            if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return make_response(jsonify({"error": "Invalid email format"}), 400)

            # Check if email already exists in database
            existing_email = CustomerEmails.query.filter_by(email=email).first()
            if existing_email:
                return make_response(jsonify({"error": "Email already exists"}), 409)

            # Create a new CustomerEmails object
            new_email = CustomerEmails(email=email)
            db.session.add(new_email)
            db.session.commit()

            return make_response(jsonify({"message": "Email added successfully"}), 201)

        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        

@ns.route("/products")
class NewProduct(Resource):
    def post(self):
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = {key: request.form[key] for key in request.form}

            name = data.get('name') 
            description = data.get('description')
            brand = data.get('brand')
            category = data.get('category')
            sub_category = data.get('sub_category')
            admin_id = data.get('admin_id')

            if not all([name, description, admin_id, category, sub_category, brand]):
                return make_response(jsonify({"error": "Missing required fields"}), 400)
            
            
            new_product = Product(name=name, description=description, admin_id=admin_id, category=category, sub_category=sub_category, brand=brand)

            # Handle variations
            variations_json = data.get('variations')
            if variations_json:
                variations = json.loads(variations_json)
                for variation_data in variations:
                    size = variation_data.get('size')
                    variation_price = int(variation_data.get('price'))
                    new_product.add_variation(size=size, price=variation_price)

            db.session.add(new_product)
            db.session.commit()

            # save images
            images = request.files.getlist("images")
            new_product.save_images(images, 'vitapharms3')

            db.session.commit()

            return make_response(jsonify({"message": "Product created successfully"}), 201)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
    
    def get(self):
        try:
            start_time = time.time()
            logging.info('Fetching products')

            # Retrieves all the products
            products = Product.query.options(
            joinedload(Product.variations),
            joinedload(Product.images)
            ).all()

            if not products:
                return make_response(jsonify({"message": "No products found"}), 404)

            logging.info(f"Products fetched in {time.time() - start_time} seconds")
            # Products list
            products_list = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "brand": product.brand,
                    "category": product.category,
                    "sub_category": product.sub_category,
                    "admin_id": product.admin_id,
                    "variations": [],
                    "images": []
                }
                var_start_time = time.time()
                variations = ProductVariation.query.filter_by(product_id=product.id).all()
                logging.info(f"Variations fetched for product {product.id} in {time.time() - var_start_time} seconds")

                for item in variations:
                    data = {
                        "id": item.id,
                        "size": item.size,
                        "price": item.price
                    }
                    product_data["variations"].append(data)

                img_start_time = time.time()
                images = Image.query.filter_by(product_id=product.id).all()
                logging.info(f"Images fetched for product {product.id} in {time.time() - img_start_time} seconds")

                for image in images:
                    image_data = {
                        "id": image.id,
                        "url": image.url
                    }
                    product_data["images"].append(image_data)

                products_list.append(product_data)

            logging.info(f"Total request time: {time.time() - start_time} seconds")
            return make_response(jsonify(products_list), 200)
        except Exception as e:
            print("Error fetching products")
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

@ns.route( "/products/<int:productId>")
class SingleProduct(Resource):
    # @cache.cached(timeout=3600, key_prefix='single_product:%s')
    def get(self, productId):  # <-- Add productId argument here
        try:
            # Retrieve the product based on productId
            product = Product.query.get(productId)
            if not product:
                return make_response(jsonify({"message": "Product not found"}), 404)

            # Product data
            product_data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "brand": product.brand,
                "category": product.category,
                "sub_category": product.sub_category,
                "admin_id": product.admin_id,
                "deal_price": product.deal_price,
                "deal_start_time": product.deal_start_time,
                "deal_end_time": product.deal_end_time,
                "variations": [],
                "images": []
            }

            # Variations
            variations = ProductVariation.query.filter_by(product_id=product.id).all()
            for item in variations:
                data = {
                    "id": item.id,
                    "size": item.size,
                    "price": item.price
                }
                product_data["variations"].append(data)

            # Images
            images = Image.query.filter_by(product_id=product.id).all()
            for image in images:
                image_data = {
                    "id": image.id,
                    "url": image.url
                }
                product_data["images"].append(image_data)

            return make_response(jsonify(product_data), 200)
        except Exception as e:
            print("Error fetching product")
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
    def patch(self, productId):
        try:
            # Checks if product exists
            product = Product.query.get(productId)
            if not product:
                return make_response(jsonify({"error": "Product not found"}), 404)
            
            # request data
            data = request.get_json()

            # iterates through the data and updates
            for field, value in data.items():
                if field == 'deal_price':
                    product.deal_price = value
                elif field == 'deal_start_time':
                    try:
                        deal_start_time = datetime.strptime(value, "%Y-%m-%d")
                        if product.deal_end_time and deal_start_time > product.deal_end_time:
                            return make_response(jsonify({"error": "Deal start time cannot be after deal end time"}), 400)
                        product.deal_start_time = deal_start_time
                    except ValueError:
                        return make_response(jsonify({"error": "Invalid date format for deal_start_time"}), 400)
                elif field == 'deal_end_time':
                    try:
                        deal_end_time = datetime.strptime(value, "%Y-%m-%d")
                        if product.deal_start_time and deal_end_time < product.deal_start_time:
                            return make_response(jsonify({"error": "Deal end time cannot be before deal start time"}), 400)
                        product.deal_end_time = deal_end_time
                    except ValueError:
                        return make_response(jsonify({"error": "Invalid date format for deal_end_time"}), 400)
                else:
                    # hanldes other field updates too
                    setattr(product, field, value)  

            db.session.commit()

            return make_response(jsonify({"message": "Product details updated successfully"}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
            
    def delete(self, productId):
        try:
            # check if product exists
            product = Product.query.get(productId)
            if not product:
                return make_response(jsonify({"error": "Product not found"}), 404)
            
            # deletes variations
            variations = ProductVariation.query.filter_by(productId=product.id).all()
            for data in variations:
                db.session.delete(data)

            # deletes image
            images = Image.query.filter_by(productId=product.id).all()
            for image in images:
                db.session.delete(image)

            # deletes product 
            db.session.delete(product)
            db.session.commit()

            return make_response(jsonify({"message": "Product deleted successfully"}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        

@ns.route("/products/deals")
class QueryDate(Resource):
    def get(self):
        try:
            # Get the date from query parameters
            date_str = request.args.get('date')
            if not date_str:
                return make_response(jsonify({"error": "Date parameter is required"}), 400)
            
            # Convert the date from string to datetime object
            try:
                query_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return make_response(jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400)

            # Query the products with active deals on the given date
            products = Product.query.filter(
                Product.deal_price.isnot(None),
                Product.deal_start_time <= query_date,
                Product.deal_end_time >= query_date
            ).all()

            # Format the response
            products_data = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "brand": product.brand,
                    "category": product.category,
                    "sub_category": product.sub_category,
                    "admin_id": product.admin_id,
                    "deal_price": product.deal_price,
                    "deal_start_time": product.deal_start_time,
                    "deal_end_time": product.deal_end_time,
                    "variations": [],
                    "images": []
                }

                # Add variations
                variations = ProductVariation.query.filter_by(product_id=product.id).all()
                for item in variations:
                    data = {
                        "id": item.id,
                        "size": item.size,
                        "price": item.price
                    }
                    product_data["variations"].append(data)

                # Add images
                images = Image.query.filter_by(product_id=product.id).all()
                for image in images:
                    image_data = {
                        "id": image.id,
                        "url": image.url
                    }
                    product_data["images"].append(image_data)

                products_data.append(product_data)

            return make_response(jsonify(products_data), 200)
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 500)
        
# adds items to cart
@ns.route("/cart/add")
class AddToCart(Resource):
    @jwt_required(optional=True)
    def post(self):
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            session_id = get_jwt_identity()

            # Retrieve variation_id for the product
            product = Product.query.get(product_id)
            if not product or not product.variations:
                return make_response(jsonify({"error": "Product or variation not found"}), 404)
            
            # Assuming the first variation for simplicity; adjust logic as needed
            variation_id = product.variations[0].id

            # Determine if the product is on a deal
            now = datetime.now()
            if product.deal_start_time and product.deal_end_time and product.deal_start_time <= now <= product.deal_end_time:
                price = product.deal_price
            else:
                price = product.variations[0].price

            # Create a new cart item and associate it with the session ID
            cart_item = CartItem(product_id=product_id, quantity=quantity, session_id=session_id, variation_id=variation_id, price=price)
            db.session.add(cart_item)
            db.session.commit()

            return make_response(jsonify({"message": "Item added to cart successfully"}), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error":  str(e)}), 500)
    
# retrives cart contents
@ns.route("/cart")
class Cart(Resource):
    @jwt_required(optional=True)
    def get(self):
        try:

            # retrieve session token from frontend
            session_identity=get_jwt_identity()

            # filters cartitems with the session token
            cart_items = CartItem.query.filter_by(session_id=session_identity).all()

            cart_contents = []
            for item in cart_items:
                product = item.products
                variation = product.variations[0]  
                item_price = item.price * item.quantity
                
                # Fetch image data for the product
                images = Image.query.filter_by(product_id=product.id).all()
                image_data = []
                for image in images:
                    image_data.append({
                        "id": image.id,
                        "url": image.url
                    })

                cart_contents.append({
                    "product_id": item.product_id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "variation_size": variation.size,
                    "price_set": item.price,
                    "total_price": item_price,
                    "image_data": image_data
                })
            
            return make_response(jsonify(cart_contents), 200)
        except DecodeError as e:
            return make_response(jsonify({"error": "Invalid JWT token"}), 401)
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 500)
    
# updates quantity of the cartitems
@ns.route("/cart/update")
class UpdateCartItem(Resource):
    @jwt_required(optional=True)
    def post(self):
        try:
            # retrieves sessionId from cookies
            session_identity = get_session_identity()

            data = request.get_json()
            product_id = data.get('product_id')
            quantity_change = data.get('quantity_change')  

            # Retrieves the cart item associated with the session ID and product ID
            cart_item = CartItem.query.filter_by(session_id=session_identity, product_id=product_id).first()

            if cart_item:
                if cart_item.quantity is None:
                    cart_item.quantity = quantity_change
                else:
                    cart_item.quantity += quantity_change

                # Ensures that the quantity does not go below 0
                if cart_item.quantity < 0:
                    cart_item.quantity = 0

                db.session.commit()

                return make_response(jsonify({"message": "Cart item quantity updated successfully"}), 200)
            else:
                return make_response(jsonify({"error": "Cart item not found"}), 404)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
# removed cartitems   
@ns.route("/cart/remove")
class RemoveFromCart(Resource):
    @jwt_required(optional=True)
    def post(self):
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            session_id = get_jwt_identity()

            # Find the cart item associated with the session ID and product ID
            cart_item = CartItem.query.filter_by(session_id=session_id, product_id=product_id).first()

            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
                return make_response(jsonify({"message": "Item removed from cart successfully"}), 200)
            else:
                return make_response(jsonify({"error": "Cart item not found"}), 404)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
# search filter
@ns.route("/products/search")
class ProductSearch(Resource):
    def get(self):
        try:
            # gets the search query parameters
            brand = request.args.get('brand', '')
            category = request.args.get('category', '')
            sub_category = request.args.get('sub_category', '')
            name = request.args.get('name', '')

            print(f"Brand: {brand}, Category: {category}, Sub-category: {sub_category},  Name: {name}")  # Debugging line

            # Create an empty list to hold filter conditions
            filters = []

            if brand:
                filters.append(Product.brand.ilike(f"%{brand}%"))
            if category:
                filters.append(Product.category.ilike(f"%{category}%"))
            if sub_category:
                filters.append(Product.sub_category.ilike(f"%{sub_category}%"))
            if name:
                filters.append(Product.name.ilike(f"%{name}%"))

            # Use and_ to combine filters with OR conditions
            query = Product.query
            if filters:
                query = query.filter(or_(*filters))

            products = query.all()
            
            print(f"Products: {products}")

            if not products:
                return make_response(jsonify({"error": "No products found"}), 400)

            # response data
            products_list = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "brand": product.brand,
                    "category": product.category,
                    "sub-category": product.sub_category,
                    "admin_id": product.admin_id,
                    "images": []
                }
                images = Image.query.filter_by(product_id=product.id).all()
                for image in images:
                    image_data = {
                        "id": image.id,
                        "url": image.url
                    }
                    product_data["images"].append(image_data)
                products_list.append(product_data)

            return make_response(jsonify(products_list), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
# products on offer
@ns.route("/products/offer")
class ProductsOnOffer(Resource):
    def get(self):
        try:
            today = datetime.date.today()

            # queries products within the deal price dates
            products = Product.query.filter(
                Product.deal_price.isnot(None),
                Product.deal_start_time <= today,
                Product.deal_end_time >= today
            ).all()

            if not products:
                return make_response(jsonify({"message": "No products currently on offer"}), 200)

            # response data
            products_list = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "deal_price": product.deal_price, 
                    "brand": product.brand,
                    "category": product.category,
                    "sub_category": product.sub_category,
                    "admin_id": product.admin_id,
                    "images": []
                }
                images = Image.query.filter_by(product_id=product.id).all()
                for image in images:
                    image_data = {
                        "id": image.id,
                        "url": image.url
                    }
                    product_data["images"].append(image_data)
                products_list.append(product_data)

            return make_response(jsonify(products_list), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

# book appointment
@ns.route("/book")
class BookAppointment(Resource):
    def post(self):
        from app import mail
        try:

            data = request.get_json()
            customer_name = data.get('customer_name')
            customer_email = data.get('customer_email')
            customer_phone = data.get('customer_phone')
            appointment_date = data.get('appointment_date')

            if not all([customer_name, customer_email, customer_phone, appointment_date]):
                return make_response(jsonify({"error": "Missing fields"}), 400)
            
            new_appointment = Appointment(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                appointment_date=appointment_date
            )

            db.session.add(new_appointment)
            db.session.commit()
            
            # using flask-mail
            msg = Message('Appointment Booking Confirmation', sender='Vitapharm <princewalter422@gmail.com>', recipients=[customer_email])
            msg.body = f"""Hi {customer_name}, This email confirms your request for an appointment booking at Vitapharm. Kindly wait as you receive a confirmation call from us."""
            mail.send(msg)

            return make_response(jsonify({"message": "Appointment booked and confirmation email sent successfully"}), 201)
        
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
    def get(self):
        try:
            appointments = Appointment.query.all()
            if not appointments:
                return make_response(jsonify({"message": "No appointments found"}), 404)
            
            appointment_list = []
            for appointment in appointments:
                appointment_data = {
                    "id": appointment.id,
                    "customer_name": appointment.customer_name,
                    "customer_email": appointment.customer_email,
                    "customer_phone": appointment.customer_phone,
                    "date": appointment.appointment_date
                }
                appointment_list.append(appointment_data)
            return make_response(jsonify(appointment_list), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
@ns.route("/order/place")
class PlaceOrder(Resource):
    @jwt_required(optional=True)
    def post(self):
        try:
            from app import mail

            # retrieves session ID from cookies
            session_id = get_jwt_identity()

            # checks if session ID exists
            if not session_id:
                return make_response(jsonify({"error": "Session token not found"}), 400)

            # querries cart items associated with the session ID
            cart_items = CartItem.query.filter_by(session_id=session_id).all()

            # checks if there are any items in the cart
            if not cart_items:
                return make_response(jsonify({"error": "Cart is empty"}), 400)

            # gets user data from request body
            data = request.get_json()
            customerFirstName = data.get('customerFirstName')
            customerLastName = data.get('customerLastName')
            customerEmail = data.get('customerEmail')
            address = data.get('address')
            town = data.get('town')
            phone = data.get('phone')
            deliverycost = data.get('deliverycost')
            discount_code = data.get('discount_code')

            # checls if all data is provided
            if not all([customerFirstName, customerLastName, customerEmail, address, town, phone, deliverycost]):
                return make_response(jsonify({"error": "Missing user information"}), 400)
            
            discount_percentage = 0
            discount_details = ""
            if discount_code:
                discount = DiscountCode.query.filter_by(code=discount_code).first()
                if discount and discount.is_valid():
                    discount_percentage = discount.discount.percentage
                    discount_details = f"\nDiscount Code: {discount_code}\nDiscount Applied: {discount_percentage}%"
                else:
                    return make_response(jsonify({"error": "Invalid or expired discount code"}), 400)

            # creates new order
            new_order = Order(
                customerFirstName=customerFirstName,
                customerLastName=customerLastName,
                customerEmail=customerEmail,
                address=address,
                town=town,
                phone=phone,
                deliverycost=deliverycost
            )
            db.session.add(new_order)

            # calculates total order value
            total_price = deliverycost
            for cart_item in cart_items:
                item_price = cart_item.price * cart_item.quantity
                total_price += item_price

            if discount_percentage > 0:
                total_price = total_price * (1 - discount_percentage / 100)

            # creates order items for each item
            for cart_item in cart_items:
                new_order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity
                )
                db.session.add(new_order_item)

            # email 
            order_details = f"""
            Customer Name: {customerFirstName} {customerLastName}
            Customer Email: {customerEmail}
            Customer Phone: {phone}
            Customer Address: {address}
            Town: {town}

            Order Items:
            """
            for cart_item in cart_items:
                product = cart_item.products
                variation = cart_item.variation
                order_details += f"\t- {product.name} ({variation.size}) (x{cart_item.quantity}) - Ksh{cart_item.price:.2f}\n"

            order_details += f"\nDelivery Cost: Ksh {deliverycost:.2f}"
            if discount_details:
                order_details += discount_details
            order_details += f"\nTotal Price: Ksh {total_price:.2f}"

            # send email notification
            msg = Message('New Order Placed!', sender='Vitapharm <princewalter422@gmail.com>', recipients=[customerEmail])
            msg.body = order_details
            mail.send(msg)

            # deletes cart items after order placement in the db
            for cart_item in cart_items:
                db.session.delete(cart_item)

            db.session.commit()

            # sends response with order details
            return make_response(jsonify({
                "message": "Order placed successfully",
                "order_id": new_order.id,
                "total_price": total_price
            }), 201)

        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
@ns.route('/verify-payment')
class VerifyPayment(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        reference = data.get('reference')
        order_id = data.get('order_id')

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
        result = response.json()

        if result['status'] and result['data']['status'] == 'success':
            try:
                order = Order.query.filter_by(id=order_id).first()
                if order:
                    order.payment_reference = reference
                    order.status = 'Paid'
                    db.session.commit()

                    return make_response(jsonify({"message": "Payment verified successfully", "order_id": order.id}), 200)
                else:
                    return make_response(jsonify({"error": "Order not found"}), 404)
            except Exception as e:
                db.session.rollback()
                return make_response(jsonify({"error": str(e)}), 500)
        else:
            return make_response(jsonify({"error": "Payment verification failed"}), 400)

        
    
@ns.route('/webhook')
class PaystackWebhook(Resource):
    def post(self):
        from app import mail, app
        try:
            if not verify_paystack_signature(request):
                app.logger.warning("Invalid Paystack signature")
                return make_response(jsonify({"error": "Invalid signature"}), 400)
            
            data = request.get_json()

            if data['event'] == 'charge.success':
                reference = data['data']['metadata']['order_id']
                order = Order.query.filter_by(id=reference).first()
                app.logger.info(f"Payment reference received: {reference}")

                if order:
                    # Ensure the payment was recently processed (within 5 minutes)
                    payment_time_str = data['data']['paidAt']
                    payment_time = datetime.strptime(payment_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

                    # Convert current time to UTC for comparison
                    current_time = datetime.now(timezone.utc)

                    time_difference = current_time - payment_time

                    if time_difference.total_seconds() <= 30:  # 300 seconds = 5 minutes
                        order.status = 'Paid'
                        db.session.commit()

                        # Send email notification
                        order_details = f"""
                        Customer Name: {order.customerFirstName} {order.customerLastName}
                        Customer Email: {order.customerEmail}
                        Customer Phone: {order.phone}
                        Customer Address: {order.address}
                        Town: {order.town}

                        Order Items:
                        """
                        for order_item in order.orderitems:
                            product_name = order_item.product.name if order_item.product else "Product Not Available"
                            quantity = order_item.quantity
                            price = order_item.product.deal_price if (order_item.product and order_item.product.deal_price is not None) else 0.0
                            order_details += f"\t- {product_name} (x{quantity}) - Ksh{price:.2f}\n"

                        order_details += f"\nDelivery Cost: Ksh {order.deliverycost:.2f}"
                        if order.discount_code:
                            order_details += f"\nDiscount Code: {order.discount_code}"
                        order_details += f"\nTotal Price: Ksh {order.total_price:.2f}"

                        msg = Message('Payment Successful!', sender='Vitapharm <princewalter422@gmail.com>', recipients=[order.customerEmail])
                        msg.body = order_details
                        mail.send(msg)

                        return make_response(jsonify({"message": "Webhook processed successfully"}), 200)
                    else:
                        return make_response(jsonify({"error": "Payment processed outside allowable time window"}), 400)
                else:
                    logger.warning(f"Order not found for payment reference: {reference}")
                    return make_response(jsonify({"error": "Order not found"}), 404)
            else:
                logger.warning(f"Unhandled event received: {data['event']}")
                return make_response(jsonify({"error": "Event not handled"}), 400)

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return make_response(jsonify({"error": "An error occurred while processing the webhook"}), 500)
        
@ns.route('/create-order')
class CreatesOrderIdTransaction(Resource):
    def post(self):
        data = request.get_json()

        discount_code = data.get('discount_code')
        discount_percentage = 0.0
        if discount_code:
            discount = DiscountCode.query.filter_by(code=discount_code).first()
            if discount and discount.is_valid():
                discount_percentage = discount.discount_percentage

        # Calculate discounted total price
        total_price = data['total'] * (1 - discount_percentage / 100)

        order = Order(
            customerFirstName=data['customerFirstName'],
            customerLastName=data['customerLastName'],
            customerEmail=data['customerEmail'],
            town=data['town'],
            phone=data['phone'],
            address=data['address'],
            deliverycost=data['deliverycost'],
            status='Pending',
            discount_code=discount_code,
            total_price=total_price
        )
        db.session.add(order)
        db.session.commit()

        return make_response(jsonify({"order_id": order.id}), 201)

@ns.route("/discount/add")
class AddDiscount(Resource):
    def post(self):
        data = request.get_json()
        code = data.get('code')
        discount_percentage = data.get('discount_percentage')
        expiration_date = data.get('expiration_date')

        if not all([code, discount_percentage, expiration_date]):
            return make_response(jsonify({"error": "Missing discount code information"}), 400)
        
        expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        new_discount = DiscountCode(
            code=code,
            discount_percentage=discount_percentage,
            expiration_date=expiration_date
        )
        db.session.add(new_discount)
        db.session.commit()

        return make_response(jsonify({"message": "Discount code added successfully"}), 201)
    
@ns.route("/discount/validate/<string:code>")
class ValidateDiscount(Resource):
        def get(self, code):
            discount = DiscountCode.query.filter_by(code=code).first()
            if discount:
                now = datetime.now(timezone.utc)
                expiration_date = discount.expiration_date.replace(tzinfo=timezone.utc)
                if now < expiration_date:
                    return make_response(jsonify({"discount_percentage": discount.discount_percentage}), 200)
            return make_response(jsonify({"error": "Invalid or expired discount code"}), 404)



    