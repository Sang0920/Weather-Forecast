# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
# from os import path
# from flask_login import UserMixin
# from common_bp import common_bp


# class Base(DeclarativeBase):
#     pass

# DB_NAME = 'database.db'
# db = SQLAlchemy(model_class=Base)

# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(100), unique=True, nullable=False)
#     fav_city = db.Column(db.String(100), nullable=False)
#     is_subscribed = db.Column(db.Boolean, default=False)
#     confirmed = db.Column(db.Boolean, default=False)
#     subscribe_token = db.Column(db.String(100), unique=True)
#     subscribe_token_expiration = db.Column(db.DateTime)
#     unsubscribe_token = db.Column(db.String(100), unique=True)

# def create_app():
#     app = Flask(__name__)
#     app.config['BASE_URL'] = 'http://api.weatherapi.com/v1'
#     app.config['SERVER_NAME'] = 'localhost:5000'
#     app.config['SECRET_KEY'] = 'sang0920'
#     app.config['MAIL_SERVER'] = 'smtp.gmail.com'
#     app.config['MAIL_PORT'] = 465
#     app.config['MAIL_USE_SSL'] = True
#     app.config['MAIL_USE_TLS'] = False
#     app.config['MAIL_USERNAME'] = 'dts@aes.edu.sg'
#     app.config['MAIL_PASSWORD'] = 'moqg tbnf cvot qihk'
#     app.config['API_KEY'] = '0bbe4606d2414828af6105401242007'
#     app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
#     app.register_blueprint(common_bp, url_prefix='/common')
#     create_database(app)
#     return app

# def create_database(app):
#     db.init_app(app)
#     if not path.exists(DB_NAME):
#         with app.app_context():
#             db.create_all()
