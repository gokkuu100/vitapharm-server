from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_restx import Api
from api.routes import ns as routes_ns
from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db
from dotenv import load_dotenv
from datetime import timedelta, datetime
import os
import secrets

import requests
from requests.auth import HTTPBasicAuth
import base64

import boto3

# Loads dotenv file
load_dotenv()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 10240 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['JWT_COOKIE_CSRF_PROTECT'] = False 

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
))
# cache.init_app(app)
mail = Mail(app)

s3 = boto3.client('s3')
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

CORS(app, supports_credentials=True)
api = Api(app, title="Vitapharm API", description="List of available endpoints for vitapharm server", prefix='/api')

api.add_namespace(routes_ns)

# run ngrok: ngrok http http://localhost:5000
my_endpoint = "https://3482-197-237-11-90.ngrok-free.app"

@app.route("/prince")
def home():
    return "Hello it's Prince"

# stkpush?phone=254796564749&amount=1
@app.route("/stkpush", methods=["POST"])
def MpesaExpress():
    amount = request.args.get('amount')
    phone = request.args.get('phone')

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
        "CallBackURL": f"{my_endpoint}/callback",
        "AccountReference": "VitapharmPayment",
        "TransactionDesc": "Test"
    }
    response = requests.post(endpoint, json=data, headers=headers)
    print("Request Data:", data)  # Debugging request data
    print("Response Data:", response.json())
    return response.json()

# mpesa-callback
@app.route("/callback", methods=["POST"])
def callback_url():
    data = request.get_json()
    print(data)
    return make_response(jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200)

# getAccessToken
def getAccessToken():
    consumer_key = "xyyfojxRcUqE57AMT1qAlc6WLKSXZGGzwUReLA2uCQAbmqaN"
    consumer_secret = "cl8uGswLYcvNAEQZDQxLBfadKxJXp8oMANWy4P8OTqdcT7V8vpDjckWyDxzAYwgZ"
    api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    my_access_token = r.json()['access_token']
    return my_access_token

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)



