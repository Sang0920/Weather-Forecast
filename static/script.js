let city_memory = null;

document.addEventListener('DOMContentLoaded', function() {
    getDefaultWeather();
    loadWeatherHistory();
});

document.getElementById('search-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        getWeather();
    }
});

document.getElementById('search-btn').addEventListener('click', getWeather);
document.getElementById('load-more-btn').addEventListener('click', loadMoreForecast);
document.getElementById('current-location-btn').addEventListener('click', getGPSLocation);
document.getElementById('subscribe-form').addEventListener('submit', subscribe);

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
    if (city === '') {
        alert('City name is required!');
        return;
    }

    const response = await fetch('/check_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ city })
    });
    const data = await response.json();
    if (data.error) {
        alert("Invalid location!\n" + data.error.message);
        return;
    }

    const wResponse = await fetch('/get_weather', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ city })
    });
    const wData = await wResponse.json();
    saveWeatherHistory(wData);
    loadWeatherHistory();
    displayWeather(wData);
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

function displayWeather(data) {
    document.getElementById('city-name').textContent = `${data.location.name} (${data.location.localtime})`;
    document.getElementById('temperature').textContent = `${data.current.temp_c}°C`;
    document.getElementById('wind-speed').textContent = `${data.current.wind_kph} KPH`;
    document.getElementById('humidity').textContent = `${data.current.humidity}%`;
    document.getElementById('weather-condition').textContent = data.current.condition.text;
    document.getElementById('weather-icon').src = `https:${data.current.condition.icon}`;
}

function displayForecast(data) {
    const forecastContainer = document.getElementById('forecast-container');
    forecastContainer.innerHTML = '';
    data.forecast.forecastday.forEach(day => {
        const forecastCard = document.createElement('div');
        forecastCard.className = 'forecast-card card mb-3';
        forecastCard.style = "width: 18rem;";
        forecastCard.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${day.date}</h5>
                <p class="card-text"><img src="https:${day.day.condition.icon}" alt="Weather icon"></p>
                <p class="card-text">Temp: ${day.day.avgtemp_c}°C</p>
                <p class="card-text">Wind: ${day.day.maxwind_kph} KPH</p>
                <p class="card-text">Humidity: ${day.day.avghumidity}%</p>
                <p class="card-text">Condition: ${day.day.condition.text}</p>
            </div>
        `;
        forecastContainer.appendChild(forecastCard);
    });
}

async function loadWeatherHistory() {
    const response = await fetch('/get_weather_history');
    const data = await response.json();
    const historyContainer = document.getElementById('history-container');
    historyContainer.innerHTML = '';
    data.forEach(data => {
        const historyCard = document.createElement('div');
        historyCard.className = 'history-card card mb-3';
        historyCard.style = "width: 18rem;";
        historyCard.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${data.location.name}</h5>
                <p class="card-text">Temp: ${data.current.temp_c}°C</p>
                <p class="card-text">Wind: ${data.current.wind_kph} KPH</p>
                <p class="card-text">Humidity: ${data.current.humidity}%</p>
                <p class="card-text">Condition: ${data.current.condition.text}</p>
            </div>
        `;
        historyContainer.appendChild(historyCard);
    });
}