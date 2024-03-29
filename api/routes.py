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
            return make_response(jsonify({"error": str(e)}), 500)
        

            
@ns.route("/create")
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
        


