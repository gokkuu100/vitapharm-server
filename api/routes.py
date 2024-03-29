from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace
from flask_jwt_extended import create_access_token
from datetime import datetime
from flask_bcrypt import Bcrypt
from models import Admin, db, Product, Image
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
            admin_id = data.get('admin_id')

            if not all([name, description, price, quantity, admin_id]):
                return make_response(jsonify({"error": "Missing required fields"}), 400)
            
            
            new_product = Product(name=name, description=description, price=price, quantity=quantity, admin_id=admin_id)

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

        


