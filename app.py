from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from api.routes import ns as routes_ns
from flask import Flask
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db
from dotenv import load_dotenv
from datetime import timedelta
import os
import secrets
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
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 300
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20


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

@app.route("/prince")
def home():
    return "Hello it's Prince"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)



