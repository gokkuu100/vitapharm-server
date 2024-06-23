from flask import request, jsonify, make_response, session
from flask_restx import Resource, Namespace
from flask_mail import Message
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token
from jwt.exceptions import DecodeError
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from models import Admin, db, Product, Image, CartItem, Appointment, Order, OrderItem, ProductVariation
import datetime
import json
import secrets
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import logging
import time
import requests
from requests.auth import HTTPBasicAuth
import base64

ns = Namespace("vitapharm", description="CRUD endpoints")
bcrypt = Bcrypt()


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

        
            # Create a new cart item and associate it with the session ID
            cart_item = CartItem(product_id=product_id, quantity=quantity, session_id=session_id, variation_id=variation_id)
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
            print(session_identity)

            # filters cartitems with the session token
            cart_items = CartItem.query.filter_by(session_id=session_identity).all()

            cart_contents = []
            for item in cart_items:
                product = item.products
                variation = product.variations[0]  
                item_price = variation.price * item.quantity
                
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
                    "variation_price": variation.price,
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

            # checls if all data is provided
            if not all([customerFirstName, customerLastName, customerEmail, address, town, phone, deliverycost]):
                return make_response(jsonify({"error": "Missing user information"}), 400)

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
                variation = cart_item.variation
                item_price = variation.price * cart_item.quantity
                total_price += item_price

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
                order_details += f"\t- {product.name} ({variation.size}) (x{cart_item.quantity}) - Ksh{variation.price:.2f}\n"

            order_details += f"\nDelivery Cost: Ksh {deliverycost:.2f}"
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
        
@ns.route("/order/pay")
class LipaNaMpesa(Resource):
    @jwt_required(optional=True)
    def post(self):
        try:
            # retrieves session ID from cookies
            session_id = get_jwt_identity()

            # checks if session ID exists
            if not session_id:
                return make_response(jsonify({"error": "Session token not found"}), 400)

            # queries cart items associated with the session ID
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

            # checks if all data is provided
            if not all([customerFirstName, customerLastName, customerEmail, address, town, phone, deliverycost]):
                return make_response(jsonify({"error": "Missing user information"}), 400)

            # calculates total order value
            total_price = deliverycost
            for cart_item in cart_items:
                variation = cart_item.variation
                item_price = variation.price * cart_item.quantity
                total_price += item_price

            # creates new order (not yet saved to DB)
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
            db.session.flush()  # Ensure new_order.id is available

            # initiate STK Push
            response = self.send_stk_push(phone, total_price, new_order.id)

            if response.get("ResponseCode") == "0":
                # save order temporarily
                db.session.commit()

                return make_response(jsonify({
                    "message": "STK Push initiated successfully. Awaiting payment confirmation.",
                    "order_id": new_order.id,
                    "total_price": total_price
                }), 200)
            else:
                db.session.rollback()
                return make_response(jsonify({"error": "Failed to initiate STK Push"}), 500)

        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        
    def send_stk_push(self, phone, amount, order_id):
        try:
            endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            access_token = getAccessToken()
            headers = {"Authorization": "Bearer %s" % access_token}
            time = datetime.now()
            timestamp = time.strftime("%Y%m%d%H%M%S")
            password = "174379" + "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919" + timestamp
            password = base64.b64encode(password.encode('utf-8')).decode('utf-8')

            data = {
                "BusinessShortCode": "174379",
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone,
                "PartyB": "174379",
                "PhoneNumber": phone,
                "CallBackURL": "http://server-env.eba-8hpawwgj.eu-north-1.elasticbeanstalk.com/api/vitapharm/callback",
                "AccountReference": "VitapharmPayment",
                "TransactionDesc": "Test"
            }
            response = requests.post(endpoint, json=data, headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("ResponseCode") == "0":
                    # Save CheckoutRequestID to the corresponding Order
                    order = Order.query.get(order_id)
                    order.checkout_request_id = response_data.get("CheckoutRequestID")
                    db.session.commit()
            return response.json()
        
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}

@ns.route("/callback", methods=["POST"])
class CallBackURL(Resource):
    def callback_url():
        try:
            data = request.get_json()
            print("CallbackData:", data)

            # Extract relevant information from the callback
            result_code = data["Body"]["stkCallback"]["ResultCode"]
            checkout_request_id = data["Body"]["stkCallback"]["CheckoutRequestID"]

            if result_code == 0:
                # Payment successful
                # Use CheckoutRequestID to find the corresponding order
                order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()

                if not order:
                    return make_response(jsonify({"error": "Order not found"}), 404)

                # Update order status and save transaction details
                order.mpesa_receipt_number = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"][1]["Value"]
                order.transaction_date = data["Body"]["stkCallback"]["CallbackMetadata"]["Item"][2]["Value"]
                order.status = "Paid"  # Update with your own order status logic

                db.session.commit()

                # Send order confirmation email
                send_order_confirmation_email(order)

                # Return success response to Safaricom
                return make_response(jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200)
            else:
                # Payment failed
                return make_response(jsonify({"ResultCode": result_code, "ResultDesc": data["Body"]["stkCallback"]["ResultDesc"]}), 200)
            
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 500)

def send_order_confirmation_email(order):
    from app import mail

    # Prepare order details for email
    order_details = f"""
    Payment by MPESA

    Customer Name: {order.customerFirstName} {order.customerLastName}
    Customer Email: {order.customerEmail}
    Customer Phone: {order.phone}
    Customer Address: {order.address}
    Town: {order.town}

    Order Items:
    """
    for order_item in order.orderitems:
        product = order_item.product
        variation = order_item.variation
        order_details += f"\t- {product.name} ({variation.size}) (x{order_item.quantity}) - Ksh{variation.price:.2f}\n"

    order_details += f"\nDelivery Cost: Ksh {order.deliverycost:.2f}"
    order_details += f"\nTotal Price: Ksh {order.total_price:.2f}"

    # Send email notification
    msg = Message('New Order Placed!', sender='Vitapharm <princewalter422@gmail.com>', recipients=[order.customerEmail])
    msg.body = order_details
    mail.send(msg)
    
    
        