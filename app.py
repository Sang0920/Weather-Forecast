from datetime import datetime, timedelta
import requests
from flask import render_template, request, jsonify, url_for
# import __init__
import json
from flask_mail import Mail, Message
# from __init__ import db, User
from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from os import path
from flask_login import UserMixin
# from .common_bp import common_bp
from common_bp import common_bp

class Base(DeclarativeBase):
    pass

DB_NAME = 'database.db'
db = SQLAlchemy(model_class=Base)

# class User(db.Model, UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(100), unique=True)
#     fav_city = db.Column(db.String(100))
#     is_subscribed = db.Column(db.Boolean, default=False)

# class Subscription(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(100), unique=True)
#     city = db.Column(db.String(100))
#     confirmed = db.Column(db.Boolean, default=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    fav_city = db.Column(db.String(100), nullable=False)
    is_subscribed = db.Column(db.Boolean, default=False)
    confirmed = db.Column(db.Boolean, default=False)
    subscribe_token = db.Column(db.String(100), unique=True)
    subscribe_token_expiration = db.Column(db.DateTime)
    unsubscribe_token = db.Column(db.String(100), unique=True)

def create_app():
    app = Flask(__name__)
    app.config['BASE_URL'] = 'http://api.weatherapi.com/v1'
    app.config['SERVER_NAME'] = 'localhost:5000'
    app.config['SECRET_KEY'] = 'sang0920'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USERNAME'] = 'dts@aes.edu.sg'
    app.config['MAIL_PASSWORD'] = 'moqg tbnf cvot qihk'
    app.config['API_KEY'] = '0bbe4606d2414828af6105401242007'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.register_blueprint(common_bp, url_prefix='/common')
    create_database(app)
    return app

def create_database(app):
    db.init_app(app)
    if not path.exists(DB_NAME):
        with app.app_context():
            db.create_all()

app = create_app()
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_weather', methods=['POST'])
def get_weather():
    city = request.json.get('city')
    response = requests.get(f'{app.config['BASE_URL']}/current.json', params={
        'key': app.config['API_KEY'],
        'q': city
    })
    data = response.json()
    return jsonify(data)

@app.route('/get_forecast', methods=['POST'])
def get_forecast():
    city = request.json['city']
    days = request.json['days']
    response = requests.get(f'{app.config['BASE_URL']}/forecast.json', params={
        'key': app.config['API_KEY'],
        'q': city,
        'days': days
    })
    data = response.json()
    return jsonify(data)

def get_city_by_ip(ip):
    response = requests.get(f'{app.config['BASE_URL']}/ip.json', params={
        'key': app.config['API_KEY'],
        'q': ip
    })
    data = response.json()
    return data['city']

@app.route('/get_location', methods=['POST'])
def get_location():
    ip = request.json['ip']
    city = get_city_by_ip(ip)
    return jsonify({'city': city})

@app.route('/save_weather_history', methods=['POST'])
def save_weather_history():
    """
    Save a weather history to cookies.
    """
    data = request.json
    data = data['data']
    print("Data: ", data)
    print("Location: ", data['location']['name'])
    history = request.cookies.get('weatherHistory')
    history = history and json.loads(history) or []
    for h in history:
        if h['location']['name'] == data['location']['name']:
            return 'Already saved', 200
    history.insert(0, data)
    if len(history) > 3:
        history.pop()
    response = jsonify(history)
    response.set_cookie('weatherHistory', json.dumps(history), max_age=60*60*24)
    return response

@app.route('/get_weather_history', methods=['GET'])
def get_weather_history():
    history = request.cookies.get('weatherHistory')
    return history and history or '[]'

@app.route('/get_location_by_gps', methods=['POST'])
def get_location_by_gps():
    lat = request.json['lat']
    lon = request.json['lon']
    response = requests.get(f'{app.config['BASE_URL']}/current.json', params={
        'key': app.config['API_KEY'],
        'q': f'{lat},{lon}'
    })
    data = response.json()
    print("GPS Data: ", data)
    return jsonify({'city': data['location']['name']})

@app.route('/check_location', methods=['POST'])
def check_location():
    city = request.json['city']
    response = requests.get(f'{app.config['BASE_URL']}/current.json', params={
        'key': app.config['API_KEY'],
        'q': city
    })
    data = response.json()
    return jsonify(data)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.json['email']
    city = request.json['city']

    user = User.query.filter_by(email=email).first()
    if user and user.is_subscribed:
        return jsonify({"message": "Already subscribed!"})

    token = serializer.dumps(email, salt='email-confirmation-salt')
    unsubscribe_token = serializer.dumps(email, salt='unsubscribe-salt')
    subscribe_token_expiration = datetime.now() + timedelta(days=1)
    confirm_url = url_for('confirm_subscription', token=token, _external=True)

    msg = Message('Weather Subscription Confirmation', recipients=[email], sender=app.config['MAIL_USERNAME'])
    msg.body = f"You have subscribed to weather updates for {city}.\nClick the link below to confirm your subscription:\n{confirm_url}"

    if not user:
        user = User(email=email, fav_city=city, is_subscribed=True, subscribe_token=token, subscribe_token_expiration=subscribe_token_expiration, unsubscribe_token=unsubscribe_token)
        db.session.add(user)
    else:
        user.is_subscribed = True
        user.fav_city = city
        user.subscribe_token = token

    try:
        mail.send(msg)
        db.session.commit()
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send confirmation email.'}), 500

    return jsonify({'message': f'Confirmation sent to your email address: {email}'}), 200

@app.route('/confirm_subscription/<token>')
def confirm_subscription(token):
    user = User.query.filter_by(subscribe_token=token).first()
    error_message = jsonify({'message': 'The confirmation link is invalid or has expired.'}), 400
    if user.subscribe_token_expiration < datetime.now():
        db.session.delete(user)
        return error_message
    if not user:
        return error_message

    user.confirmed = True
    user.subscribe_token = None
    db.session.commit()

    return jsonify({'message': 'Subscription confirmed!'}), 200

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    user = User.query.filter_by(unsubscribe_token=token).first()
    if not user:
        return jsonify({'message': 'Subscription not found.'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'Unsubscribed successfully!'}), 200

def send_daily_forecast():
    print("Sending daily forecast...")
    with app.app_context():
        users = User.query.filter_by(is_subscribed=True, confirmed=True).all()
        print("Users count: ", len(users))
        for user in users:
            city = user.fav_city
            email = user.email
            response = requests.get(f"{app.config['BASE_URL']}/forecast.json", params={
                'key': app.config['API_KEY'],
                'q': city,
                'days': 1
            })
            data = response.json()
            forecast = data['forecast']['forecastday'][0]['hour']
            forecast_9_to_24 = [{
                'time': hour['time'].split(' ')[1],
                'temp': hour['temp_c'],
                'condition': hour['condition']['text']
            } for hour in forecast if 9 <= int(hour['time'].split(' ')[1].split(':')[0]) <= 24]

            token = user.unsubscribe_token
            unsubscribe_url = url_for('unsubscribe', token=token, _external=True)

            html_content = render_template('daily.html', city=city, forecast_9_to_24=forecast_9_to_24, unsubscribe_url=unsubscribe_url)

            msg = Message('Daily Weather Forecast', recipients=[email], sender=app.config['MAIL_USERNAME'])
            msg.html = html_content  # Set the email content to the rendered HTML

            try:
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send forecast email to {email}: {e}")

if __name__ == '__main__':
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Ho_Chi_Minh'))
    scheduler.add_job(send_daily_forecast, trigger='cron', hour=8, minute=0)
    scheduler.add_job(send_daily_forecast, trigger='cron', hour=17, minute=47)
    scheduler.start()
    app.run(debug=False)