from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace
from flask_jwt_extended import create_access_token
from datetime import datetime
from flask_bcrypt import Bcrypt
from models import Admin, db, Product, Image, CartItem
import base64

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
            quantity = data.get('quantity')
            category = data.get('category')
            sub_category = data.get('sub_category')
            admin_id = data.get('admin_id')

            if not all([name, description, price, quantity, admin_id, category, sub_category]):
                return make_response(jsonify({"error": "Missing required fields"}), 400)
            
            
            new_product = Product(name=name, description=description, price=price, quantity=quantity, admin_id=admin_id, category=category, sub_category=sub_category)

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
            field = data.get('field')  # Field to update
            value = data.get('value')  # New value 

            # updates the specific field
            if field == 'name':
                product.name = value
            elif field == 'description':
                product.description = value
            elif field == 'price':
                product.price = value
            elif field == 'quantity':
                product.quantity = value
            elif field == 'admin_id':
                product.admin_id = value
            else:
                return make_response(jsonify({"error": "Invalid field provided"}), 400)

            db.session.commit()

            return make_response(jsonify({"message": f"{field} updated successfully"}), 200)
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
            # retrieves sessionid from the cookies
            session_id = request.cookies.get("session_id")

            data = request.get_json()
            product_id = data.get('product_id')
            quantity_change = data.get('quantity_change')  # This can be positive or negative

            # Retrieve the cart item associated with the session ID and product ID
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
        
    

