from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_mail import Mail
import os
from dotenv import load_dotenv
# Load biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/OpenBanking?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
# configuration of mail 
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ctvayno@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
class Base(DeclarativeBase):
    __abstract__ = True

db = SQLAlchemy(app, model_class=Base)

login_manager = LoginManager(app)

mail = Mail(app)

# Để các module khác có thể import được
__all__ = ["app", "db","login_manager","mail"]
