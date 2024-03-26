from flask import request, jsonify, make_response
from flask_restx import Resource, Namespace
from flask_jwt_extended import create_access_token
from datetime import datetime
import base64

ns = Namespace("vitapharm", description="CRUD endpoints")

@ns.route("/home")
class Hello(Resource):
    def get(self):
        return "Welcome to the first route"

