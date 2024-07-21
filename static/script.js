let city_memory = null;

document.addEventListener('DOMContentLoaded', function() {
    getDefaultWeather();
    loadWeatherHistory();
});

document.getElementById('search-btn').addEventListener('click', getWeather);
document.getElementById('load-more-btn').addEventListener('click', loadMoreForecast);
document.getElementById('current-location-btn').addEventListener('click', getGPSLocation);
document.getElementById('subscribe-form').addEventListener('submit', subscribe);

/*
@app.route('/subscribe', methods=['POST', 'GET'])
def subscribe():
    """
    Subscribe and send email confirmation.
    """
    email = request.json['email']
    city = request.json['city']
    # send email confirmation link
    mail = Mail(app)
    msg = Message('Weather Subscription Confirmation', recipients=[email])
    msg.body = f"You have subscribed to weather updates for {city}.Click the link below to confirm your subscription: http://{HOST}/confirm_subscription?email={email}&city={city}"
    # send email and check if it was sent
    try:
        mail.send(msg)
    except Exception as e:
        print(e)
        return 'Failed to send email', 500
    return 'Email sent', 200
*/

async function subscribe() {
    event.preventDefault();
    const email = document.getElementById('subscribe-email').value;
    const subscribeCity = document.getElementById('subscribe-city').value;

    if (email === '') {
        alert('Email address is required!');
        return;
    }

    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    if (!emailRegex.test(email)) {
        alert('Invalid email address!');
        return;
    }

    if (subscribeCity === '') {
        alert('City is required!');
        return;
    }

    const checkLocationResponse = await fetch('/check_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ city: subscribeCity })
    });
    const checkLocationData = await checkLocationResponse.json();
    if (checkLocationData.error) {
        alert("Invalid location!\n" + checkLocationData.error.message);
        return;
    }

    const response = await fetch('/subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, city: subscribeCity })
    });
    const data = await response.json();
    alert(data.message);
}


function getGPSLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            const locationResponse = await fetch('/get_location_by_gps', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lat, lon })
            });
            const locationData = await locationResponse.json();
            const city = locationData.city;
            document.getElementById('search-input').value = city;
            city_memory = city;
            alert(`We detected your location using GPS as ${city}.`);

            const weatherResponse = await fetch('/get_weather', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ city })
            });
            const weatherData = await weatherResponse.json();
            saveWeatherHistory(weatherData);
            loadWeatherHistory();
            displayWeather(weatherData);
            loadForecast(city, 4);
        });
    } else {
        alert('Geolocation is not supported by this browser.');
    }
}

async function getDefaultWeather() {
    const ipResponse = await fetch('https://api.ipify.org?format=json');
    const ipData = await ipResponse.json();
    const userIp = ipData.ip;

    const locationResponse = await fetch('/get_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ip: userIp })
    });
    const locationData = await locationResponse.json();
    const city = locationData.city;
    document.getElementById('search-input').value = city;
    city_memory = city;
    alert(`We detected your location using your IP address as ${city}.`);

    const weatherResponse = await fetch('/get_weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ city })
    });
    const weatherData = await weatherResponse.json();
    saveWeatherHistory(weatherData);
    loadWeatherHistory();
    displayWeather(weatherData);
    loadForecast(city, 4);
}

async function getWeather() {
    const city = document.getElementById('search-input').value;
    city_memory = city;
    const response = await fetch('/get_weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ city })
    });
    const data = await response.json();
    saveWeatherHistory(data);
    loadWeatherHistory();
    displayWeather(data);
    loadForecast(city, 4);
}

async function loadForecast(city, days) {
    const response = await fetch('/get_forecast', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ city, days })
    });
    const data = await response.json();
    displayForecast(data);
}

async function loadMoreForecast() {
    if (city_memory == null) {
        const city = document.getElementById('search-input').value;
    }
    const city = city_memory;
    const forecastCards = document.querySelectorAll('.forecast-card').length;
    loadForecast(city, forecastCards + 4);
}

function displayWeather(data) {
    document.getElementById('city-name').textContent = `${data.location.name} (${data.location.localtime})`;
    document.getElementById('temperature').textContent = data.current.temp_c;
    document.getElementById('wind-speed').textContent = data.current.wind_kph;
    document.getElementById('humidity').textContent = data.current.humidity;
    document.getElementById('weather-condition').textContent = data.current.condition.text;
}

function displayForecast(data) {
    const forecastContainer = document.getElementById('forecast-container');
    forecastContainer.innerHTML = '';
    data.forecast.forecastday.forEach(day => {
        const forecastCard = document.createElement('div');
        forecastCard.className = 'forecast-card';
        forecastCard.innerHTML = `
            <h3>${day.date}</h3>
            <p>Temp: ${day.day.avgtemp_c}°C</p>
            <p>Wind: ${day.day.maxwind_kph} KPH</p>
            <p>Humidity: ${day.day.avghumidity}%</p>
            <p>Condition: ${day.day.condition.text}</p>
        `;
        forecastContainer.appendChild(forecastCard);
    });
}

async function saveWeatherHistory(data) {
    const response = await fetch('/save_weather_history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data })
    });
    console.log(response);
}

async function loadWeatherHistory() {
    const response = await fetch('/get_weather_history');
    const data = await response.json();
    const historyContainer = document.getElementById('history-container');
    historyContainer.innerHTML = '';
    data.forEach(data => {
        const historyCard = document.createElement('div');
        historyCard.className = 'history-card';
        historyCard.innerHTML = `
            <h3>${data.location.name}</h3>
            <p>Temp: ${data.current.temp_c}°C</p>
            <p>Wind: ${data.current.wind_kph} KPH</p>
            <p>Humidity: ${data.current.humidity}%</p>
            <p>Condition: ${data.current.condition.text}</p>
        `;
        historyContainer.appendChild(historyCard);
    });
}