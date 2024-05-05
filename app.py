from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from api.routes import ns as routes_ns
from flask import Flask
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db
from dotenv import load_dotenv
import os

# Loads dotenv file
load_dotenv()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vitapharm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 10240 * 1024
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
))
mail = Mail(app)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

CORS(app, supports_credentials=True)
api = Api(app, title="Vitapharm API", description="List of available endpoints for vitapharm server", prefix='/api')

api.add_namespace(routes_ns)

if __name__ == '__main__':
    app.run(port=os.getenv('PORT'), debug=True)



