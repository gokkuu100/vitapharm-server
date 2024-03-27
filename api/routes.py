from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace
from flask_jwt_extended import create_access_token
from datetime import datetime
from flask_bcrypt import Bcrypt
from models import Admin, db
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
            
