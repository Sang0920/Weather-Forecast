# Weather Forecast Application

The Weather Forecast Application is a comprehensive solution designed to provide users with up-to-date weather information for any city or country. This application is built with a focus on backend processing to ensure a seamless and efficient user experience. Below is an overview of the features that have been implemented, adhering to the requirements set forth.

## Features

- **Backend API Processing**: All interactions with the weather API are handled on the backend, ensuring data integrity and security.
- **City/Country Search**: Users can search for weather information by city or country, making it easy to find the weather details they need.
- **Current Weather Display**: The application displays current weather information, including temperature, wind speed, humidity, and more.
- **Weather Forecast**: Users can view the weather forecast for the next four days, with an option to load more days for extended planning.
- **Weather Information History**: Temporary weather information is saved and can be displayed again throughout the day, allowing users to revisit previous searches without re-querying.
- **Email Subscription for Daily Forecast**: Users can register to receive daily weather forecasts via email. This feature includes email confirmation to ensure user consent.
- **Deployment**: The application is deployed and accessible live, allowing users to access it from anywhere at any time.
- **Responsive Design**: The application is designed to be responsive, ensuring a seamless experience across desktops, tablets, and mobile phones.
- **Smooth Animations**: Where applicable, smooth animations enhance the user interface, providing a visually appealing experience.
- **Docker Setup**: The project is set up with Docker, simplifying the development and deployment process by ensuring consistency across environments.

## Deployment

The application is deployed and available for use. Users can access it to search for weather information, subscribe to daily forecasts, and more.

Live Deployment: [Weather-Forecast on Render](https://weather-forecast-82fr.onrender.com)

## Docker Setup

To set up your project using Docker on Ubuntu, follow these steps:

1. **Build the Docker Image:**
    ```bash
    docker build -t weather-forecast-app .
    ```

2. **Run the Docker Container:**
    ```bash
    docker run -p 5000:5000 weather-forecast-app
    ```
