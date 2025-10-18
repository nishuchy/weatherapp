from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Geocoding API (to get lat/lon from city name)
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
# Weather API
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/weather", methods=["POST"])
def get_weather():
    location = request.form.get("location")
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    # Get latitude and longitude if user entered a city name
    if not (lat and lon):
        geo_response = requests.get(GEOCODE_URL, params={"name": location, "count": 1})
        geo_data = geo_response.json()
        if "results" not in geo_data:
            return jsonify({"error": "Location not found"}), 404
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city = geo_data["results"][0]["name"]
        country = geo_data["results"][0].get("country", "")
    else:
        city = "Your Location"
        country = ""

    # Fetch weather data
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
        "timezone": "auto"
    }
    weather_response = requests.get(WEATHER_URL, params=params)
    weather_data = weather_response.json()

    if "current_weather" not in weather_data:
        return jsonify({"error": "Weather data not found"}), 404

    # Current weather
    current = weather_data["current_weather"]
    current_info = {
        "city": city,
        "country": country,
        "temp": current["temperature"],
        "windspeed": current["windspeed"],
        "description": get_weather_description(current["weathercode"])
    }

    # Forecast (next 5 days)
    forecast_data = []
    for i in range(min(5, len(weather_data["daily"]["time"]))):
        forecast_data.append({
            "date": weather_data["daily"]["time"][i],
            "temp_max": weather_data["daily"]["temperature_2m_max"][i],
            "temp_min": weather_data["daily"]["temperature_2m_min"][i],
            "description": get_weather_description(weather_data["daily"]["weathercode"][i])
        })

    return jsonify({"current": current_info, "forecast": forecast_data})


def get_weather_description(code):
    """ Map Open-Meteo weather codes to readable descriptions """
    codes = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        71: "Slight Snow Fall",
        73: "Moderate Snow Fall",
        75: "Heavy Snow Fall",
        80: "Rain Showers",
        81: "Moderate Showers",
        82: "Violent Showers",
        95: "Thunderstorm",
        99: "Thunderstorm with Hail",
    }
    return codes.get(code, "Unknown")


if __name__ == "__main__":
    app.run(debug=True)
