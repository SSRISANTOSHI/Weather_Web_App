from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import Config

# Prefer environment variable, fallback to Config
API_KEY = os.getenv("OPENWEATHER_API_KEY") or getattr(Config, "OPENWEATHER_API_KEY", None)

app = Flask(__name__)
CORS(app)

# Helper: create DB connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        return conn
    except Error as e:
        print("DB connection error:", e)
        raise

# Weather proxy endpoint
@app.route("/api/weather", methods=["GET"])
def get_weather():
    if not API_KEY:
        return jsonify({"error": "OpenWeather API key not configured."}), 500

    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"appid": API_KEY, "units": "metric"}

    if city:
        params["q"] = city
    elif lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    else:
        return jsonify({"error": "Please provide city or lat & lon."}), 400

    try:
        resp = requests.get(base_url, params=params, timeout=10)
        data = resp.json()

        # Handle OpenWeather API error messages
        if resp.status_code != 200:
            return jsonify({
                "error": data.get("message", "Failed to fetch weather"),
                "status_code": resp.status_code
            }), resp.status_code

        # Shape response to only what frontend needs
        result = {
            "name": data.get("name"),
            "weather": data.get("weather", []),
            "main": data.get("main", {}),
            "wind": data.get("wind", {}),
            "sys": data.get("sys", {}),
            "coord": data.get("coord", {})
        }
        return jsonify(result)

    except requests.exceptions.RequestException as re:
        return jsonify({"error": "Weather API request failed", "details": str(re)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected server error", "details": str(e)}), 500

# Contact/feedback endpoint (stores to MySQL)
@app.route("/api/contact", methods=["POST"])
def submit_contact():
    body = request.json
    name = body.get("name")
    email = body.get("email")
    message = body.get("message")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO feedback (name, email, message) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, email, message))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Feedback saved"}), 201
    except Exception as e:
        print("DB insert error:", e)
        return jsonify({"error": "Failed to save feedback", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)