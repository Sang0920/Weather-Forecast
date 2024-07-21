from datetime import datetime, timedelta
import requests
from flask import render_template, request, jsonify, url_for
import __init__
import json
from flask_mail import Mail, Message
from __init__ import db, User
from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = __init__.create_app()
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

# @app.route('/subscribe', methods=['POST'])
# def subscribe():
#     email = request.json['email']
#     city = request.json['city']

#     existing_subscription = Subscription.query.filter_by(email=email).first()
#     if existing_subscription:
#         return jsonify({"message": "Already subscribed!"})

#     token = serializer.dumps(email, salt='email-confirmation-salt')
#     confirm_url = url_for('confirm_subscription', token=token, _external=True)
    
#     msg = Message('Weather Subscription Confirmation', recipients=[email], sender=app.config['MAIL_USERNAME'])
#     msg.body = f"You have subscribed to weather updates for {city}.\nClick the link below to confirm your subscription:\n{confirm_url}"
    
#     try:
#         mail.send(msg)
#         new_subscription = Subscription(email=email, city=city)
#         db.session.add(new_subscription)
#         db.session.commit()
#     except Exception as e:
#         print(e)
#         return jsonify({'error': 'Failed to send confirmation email.'}), 500

#     return jsonify({'message': f'Confirmation sent to your email address: {email}'}), 200

# @app.route('/confirm_subscription/<token>')
# def confirm_subscription(token):
#     try:
#         email = serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
#     except:
#         return jsonify({'message': 'The confirmation link is invalid or has expired.'}), 400
    
#     subscription = Subscription.query.filter_by(email=email).first()
#     if not subscription:
#         return jsonify({'message': 'Subscription not found.'}), 404
    
#     subscription.confirmed = True
#     db.session.commit()
    
#     return jsonify({'message': 'Subscription confirmed!'}), 200

# @app.route('/unsubscribe', methods=['POST'])
# def unsubscribe():
#     email = request.json['email']
#     subscription = Subscription.query.filter_by(email=email).first()
#     if not subscription:
#         return jsonify({'message': 'Subscription not found.'}), 404
    
#     db.session.delete(subscription)
#     db.session.commit()
    
#     return jsonify({'message': 'Unsubscribed successfully!'}), 200

# def send_daily_forecast():
#     print("Sending daily forecast...")
#     with app.app_context():
#         subscriptions = Subscription.query.filter_by(confirmed=True).all()
#         for subscription in subscriptions:
#             city = subscription.city
#             email = subscription.email
#             response = requests.get(f"{app.config['BASE_URL']}/forecast.json", params={
#                 'key': app.config['API_KEY'],
#                 'q': city,
#                 'days': 1
#             })
#             data = response.json()
#             forecast = data['forecast']['forecastday'][0]['hour']
#             forecast_9_to_18 = [hour for hour in forecast if 9 <= int(hour['time'].split(' ')[1].split(':')[0]) <= 18]

#             forecast_message = f"Weather forecast for {city} from 9 AM to 6 PM:\n"
#             for hour in forecast_9_to_18:
#                 time = hour['time'].split(' ')[1]
#                 temp = hour['temp_c']
#                 condition = hour['condition']['text']
#                 forecast_message += f"{time}: {temp}°C, {condition}\n"
            
#             token = serializer.dumps(email, salt='unsubscribe-salt')
#             unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
#             forecast_message += f"\nTo unsubscribe from daily weather updates, click here: {unsubscribe_url}"

#             msg = Message('Daily Weather Forecast', recipients=[email], sender=app.config['MAIL_USERNAME'])
#             msg.body = forecast_message

#             try:
#                 mail.send(msg)
#             except Exception as e:
#                 print(f"Failed to send forecast email to {email}: {e}")

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

# def send_daily_forecast():
#     print("Sending daily forecast...")
#     with app.app_context():
#         users = User.query.filter_by(is_subscribed=True, confirmed=True).all()
#         print("Users count: ", len(users))
#         for user in users:
#             city = user.fav_city
#             email = user.email
#             response = requests.get(f"{app.config['BASE_URL']}/forecast.json", params={
#                 'key': app.config['API_KEY'],
#                 'q': city,
#                 'days': 1
#             })
#             data = response.json()
#             forecast = data['forecast']['forecastday'][0]['hour']
#             forecast_9_to_24 = [hour for hour in forecast if 9 <= int(hour['time'].split(' ')[1].split(':')[0]) <= 24]

#             forecast_message = f"Good morning!\nWeather forecast for {city} from 9 AM to 12 PM:\n"
#             for hour in forecast_9_to_24:
#                 time = hour['time'].split(' ')[1]
#                 temp = hour['temp_c']
#                 condition = hour['condition']['text']
#                 forecast_message += f"{time}: {temp}°C, {condition}\n"

#             token = user.unsubscribe_token
#             unsubscribe_url = url_for('unsubscribe', token=token, _external=True)
#             forecast_message += f"\nTo unsubscribe from daily weather updates, click here: {unsubscribe_url}"

#             msg = Message('Daily Weather Forecast', recipients=[email], sender=app.config['MAIL_USERNAME'])
#             msg.body = forecast_message

#             try:
#                 mail.send(msg)
#             except Exception as e:
#                 print(f"Failed to send forecast email to {email}: {e}")

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
    scheduler.add_job(send_daily_forecast, trigger='cron', hour=16, minute=0)
    scheduler.start()
    app.run(debug=False)