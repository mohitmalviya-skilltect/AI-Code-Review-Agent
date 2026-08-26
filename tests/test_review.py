import requests

API_KEY = "AIzaSyExample123456789"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMIExampleSecretKey"

def get_weather(city):
    url = "https://api.example.com/weather"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.get(url, headers=headers, timeout=10)

    return response.json()