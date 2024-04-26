from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace
from flask_mail import Message
from flask_jwt_extended import create_access_token
from datetime import datetime
from flask_bcrypt import Bcrypt
from models import Admin, db, Product, Image, CartItem, Appointment
import base64
import datetime

ns = Namespace("vitapharm", description="CRUD endpoints")
bcrypt = Bcrypt()

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
            quantity = data.get('quantity')
            category = data.get('category')
            sub_category = data.get('sub_category')
            admin_id = data.get('admin_id')

            if not all([name, description, price, quantity, admin_id, category, sub_category, brand]):
                return make_response(jsonify({"error": "Missing required fields"}), 400)
            
            
            new_product = Product(name=name, description=description, price=price, quantity=quantity, admin_id=admin_id, category=category, sub_category=sub_category, brand=brand)

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
                    "price": product.price,
                    "quantity": product.quantity,
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
            print("Error fetching products")
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

@ns.route( "/products/<int:productId>" )
class SingleProduct(Resource):
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
                "quantity": singleProduct.quantity,
                "brand": singleProduct.brand,
                "category": singleProduct.category,
                "sub-category": singleProduct.sub_category,
                "admin_id": singleProduct.admin_id,
                "images": []
            }
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
    def post(self):
        try:
            # retrieve sessionid from cookies
            session_id = request.cookies.get("session_id", None) 

            data = request.get_json()
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)

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
    def get(self):
        # retrieve sessionId from frontend
        session_id = request.args.get('session_id')  

        # filters cartitems with the sessionId
        cart_items = CartItem.query.filter_by(session_id=session_id).all()


        cart_contents = [{"product_id": item.product_id, "quantity": item.quantity} for item in cart_items]
        return make_response(jsonify(cart_contents), 200)
    
# updates quantity of the cartitems
@ns.route("/cart/update")
class UpdateCartItem(Resource):
    def post(self):
        try:
            # retrieves sessionId from cookies
            session_id = request.cookies.get("session_id")

            data = request.get_json()
            product_id = data.get('product_id')
            quantity_change = data.get('quantity_change')  

            # Retrieves the cart item associated with the session ID and product ID
            cart_item = CartItem.query.filter_by(session_id=session_id, product_id=product_id).first()

            if cart_item:
                if cart_item.quantity is None:
                    cart_item.quantity = quantity_change
                else:
                    cart_item.quantity += quantity_change

                # Ensure that the quantity does not go below 0
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
                    "quantity": product.quantity,
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
                    "quantity": product.quantity,
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
                    "customer_phone": appointment.customer_name,
                    "date": appointment.date
                }
                appointment_list.append(appointment_data)
            return make_response(jsonify(appointment_list), 200)
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)
        