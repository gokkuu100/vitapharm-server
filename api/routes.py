from flask import request, jsonify, make_response, session
from flask_restx import Resource, Namespace
from flask_mail import Message
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from jwt.exceptions import DecodeError
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from models import Admin, db, Product, Image, CartItem, Appointment, Order, OrderItem, ProductVariation
from caching import cache
import base64
import datetime
import json
import jwt
import secrets

ns = Namespace("vitapharm", description="CRUD endpoints")
bcrypt = Bcrypt()



# Generates JWT token for session
def generate_session_token():
    random_identity = secrets.token_urlsafe(16)
    expires = timedelta(hours=1)
    return create_access_token(random_identity, expires_delta=expires)

# Extracts session identity
def get_session_identity():
    return get_jwt_identity()

# JWT session-management
@ns.route("/session")
class Session(Resource):
    def get(self):
        # Generate session token for the current session
        session_token = generate_session_token()
        # Stores the session token in Flask session
        session['session_token'] = session_token
        return make_response(jsonify({"session_token": session_token}), 200)

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
            price = int(data.get('price'))
            brand = data.get('brand')
            category = data.get('category')
            sub_category = data.get('sub_category')
            admin_id = data.get('admin_id')

            if not all([name, description, price, admin_id, category, sub_category, brand]):
                return make_response(jsonify({"error": "Missing required fields"}), 400)
            
            
            new_product = Product(name=name, description=description, price=price, admin_id=admin_id, category=category, sub_category=sub_category, brand=brand)

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
            for image in images:
                if image.filename != '':
                    image_data = image.read()
                    new_image = Image(data=image_data, product_id=new_product.id)
                    db.session.add(new_image)

            db.session.commit()

            return make_response(jsonify({"message": "Product created successfully"}), 201)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
    
    @cache.cached(timeout=60*30, query_string=True)
    def get(self):
        try:
            # retrieves all the products
            products = Product.query.all()
            if not products:
                return make_response(jsonify({"message": "No products found"}), 404)
            
            # products list
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
                variations = ProductVariation.query.filter_by(product_id=product.id).all()
                for item in variations:
                    data = {
                        "id": item.id,
                        "size": item.size,
                        "price": item.price
                    }
                    product_data["variations"].append(data)
                products_list.append(product_data)

                images = Image.query.filter_by(product_id=product.id).all()
                for image in images:
                    image_data = {
                        "id": image.id,
                        "data": base64.b64encode(image.data).decode('utf-8')
                    }
                    product_data["images"].append(image_data)
                products_list.append(product_data)

            return make_response(jsonify(products_list), 200)
        except Exception as e:
            print("Error fetching products")
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

@ns.route( "/products/<int:productId>")
class SingleProduct(Resource):
    @cache.cached(timeout=3600, key_prefix='single_product:%s')
    def get(self, productId):
        try:
            # checks for specific product
            singleProduct = Product.query.get(productId)
            if not singleProduct:
                return make_response(jsonify({"error": "Product not found"}), 404)
            
            # product data
            product_data = {
                "id": singleProduct.id,
                "name": singleProduct.name,
                "description": singleProduct.description,
                "price": singleProduct.price,
                "brand": singleProduct.brand,
                "category": singleProduct.category,
                "sub-category": singleProduct.sub_category,
                "admin_id": singleProduct.admin_id,
                "variations": [],
                "images": []
            }
            # retrieves price variations
            variations = ProductVariation.query.filter_by(product_id=singleProduct.id).all()
            for item in variations:
                data = {
                    "id": item.id,
                    "size": item.size,
                    "price": item.price
                }
                product_data["variations"].append(data)
    
            # retrieves images
            images = Image.query.filter_by(product_id=singleProduct.id).all()
            for image in images:
                image_data = {
                    "id": image.id,
                    "data": base64.b64encode(image.data).decode('utf-8')
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

        
            # Create a new cart item and associate it with the session ID
            cart_item = CartItem(product_id=product_id, quantity=quantity, session_id=session_id)
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
                        "data": base64.b64encode(image.data).decode('utf-8')
                    })

                cart_contents.append({
                    "product_id": item.product_id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "variation_size": variation.size,
                    "variation_price": variation.price,
                    "total_price": item_price,
                    "image_data0": image_data
                })
            
            return make_response(jsonify(cart_contents), 200)
        except DecodeError as e:
            return make_response(jsonify({"error": "Invalid JWT token"}), 401)
        except Exception as e:
            return make_response(jsonify({"error": str(e)}), 500)
    
# updates quantity of the cartitems
@ns.route("/cart/update")
class UpdateCartItem(Resource):
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
        

        
# search filter
@ns.route("/products/search")
class ProductSearch(Resource):
    def get(self):
        try:
            # gets the search query parameters
            brand = request.args.get('brand')
            category = request.args.get('category')
            sub_category = request.args.get('sub_category')

            # queries products based on categories
            if category and sub_category:
                products = Product.query.filter_by(category=category, sub_category=sub_category).all()
            elif category:
                products = Product.query.filter_by(category=category).all()
            elif brand:
                products = Product.query.filter_by(brand=brand).all()
            else:
                return make_response(jsonify({"error": "Please provide at least a category"}), 400)

            # response data
            products_list = []
            for product in products:
                product_data = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
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
                        "data": base64.b64encode(image.data).decode('utf-8')
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
                    "price": product.price,
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
                        "data": base64.b64encode(image.data).decode('utf-8')
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
        try:
            from app import mail

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
            return make_response(jsonify( {"error": str(e)}), 500)
        
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
    def post(self):
        try:
            from app import mail

            # retrieves session ID from cookies
            session_id = request.cookies.get("session_id", None)

            # checks if session ID exists
            if not session_id:
                return make_response(jsonify({"error": "Session ID not found"}), 400)

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

            # checls if all data is provided
            if not all([customerFirstName, customerLastName, customerEmail, address, town, phone]):
                return make_response(jsonify({"error": "Missing user information"}), 400)

            # creates new order
            new_order = Order(
                customerFirstName=customerFirstName,
                customerLastName=customerLastName,
                customerEmail=customerEmail,
                address=address,
                town=town,
                phone=phone
            )
            db.session.add(new_order)

            # calculates total order value
            total_price = 0
            for cart_item in cart_items:
                product = cart_item.products
                item_price = product.price * cart_item.quantity
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
                order_details += f"\t- {product.name} (x{cart_item.quantity}) - Ksh{product.price:.2f}\n"

            order_details += f"\nTotal Price: Ksh {total_price:.2f}"

            # send email notification
            msg = Message('New Order Placed!', sender='Vitapharm <princewalter422@gmail.com>', recipients=['wkurts247@gmail.com'])
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
        