import requests
from flask import render_template, request, jsonify, url_for
import __init__
import json
from flask_mail import Mail, Message
from __init__ import db, Subscription
from itsdangerous import URLSafeTimedSerializer

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

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.json['email']
    city = request.json['city']

    existing_subscription = Subscription.query.filter_by(email=email).first()
    if existing_subscription:
        return jsonify({"message": "Already subscribed!"})

    token = serializer.dumps(email, salt='email-confirmation-salt')
    confirm_url = url_for('confirm_subscription', token=token, _external=True)
    
    msg = Message('Weather Subscription Confirmation', recipients=[email], sender=app.config['MAIL_USERNAME'])
    msg.body = f"You have subscribed to weather updates for {city}.\nClick the link below to confirm your subscription:\n{confirm_url}"
    
    try:
        mail.send(msg)
        new_subscription = Subscription(email=email, city=city)
        db.session.add(new_subscription)
        db.session.commit()
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send confirmation email.'}), 500

    return jsonify({'message': f'Confirmation sent to your email address: {email}'}), 200

@app.route('/confirm_subscription/<token>')
def confirm_subscription(token):
    try:
        email = serializer.loads(token, salt='email-confirmation-salt', max_age=3600)
    except:
        return jsonify({'message': 'The confirmation link is invalid or has expired.'}), 400
    
    subscription = Subscription.query.filter_by(email=email).first()
    if not subscription:
        return jsonify({'message': 'Subscription not found.'}), 404
    
    subscription.confirmed = True
    db.session.commit()
    
    return jsonify({'message': 'Subscription confirmed!'}), 200

# send daily weather forecast information via email addresses.
def send_daily_forecast():
    subscriptions = Subscription.query.all()
    for subscription in subscriptions:
        response = requests.get(f'{app.config['BASE_URL']}/forecast.json', params={
            'key': app.config['API_KEY'],
            'q': subscription.city,
            'days': 1
        })
        data = response.json()
        forecast = data['forecast']['forecastday'][0]
        msg = Message('Daily Weather Forecast', recipients=[subscription.email], sender=app.config['MAIL_USERNAME'])
        msg.body = f"Good morning! Here's the weather forecast for today in {subscription.city}:\n{forecast['day']['condition']['text']}, {forecast['day']['maxtemp_c']}°C"
        mail.send(msg)
    
    return jsonify({'message': 'Daily forecast sent to all subscribers.'}), 200

if __name__ == '__main__':
    # send daily forecast at 8:00 AM
    with app.app_context():
        send_daily_forecast()
        
    app.run(debug=True)