# Building Useful Tools with APIs

import os
import requests
from dotenv import load_dotenv
load_dotenv

api_key = os.getenv("OPENWETHER_API_KEY")

#city = input("city:").strip()
city = "Lagos"

def get_weather(city):   
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_country_info(country_code):
    url = f"https//:restcountries.com/v3.1/alpha/{country_code}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None 

def run_tool():
    print("TRAVEL WEATHER TOOL")
    print("********************")
    
    
    if not city:
        print("No city entered. Exiting.")
        return
    print("Fetching data for {city}...")

    weather_data = get_weather(city)

    if not weather_data:
        print(f"Could not find weather data for {city}. Check and try again")
        return

    county_code = weather_data['sys']['country']
    country_data = get_country_info(county_code)

    print(f"\n=== {city.title()}, {county_code}===")
    print(f"Temperature : {weather_data['main']['temp']}C")
    print(f"Condition   : {weather_data['weather'][0]['description'].tittle()}")
    print(f"Humidity    : {weather_data['main']['humidity']}%")
    print(f"Wind speed  : {weather_data['wind']['speed']}m/s")

    if country_data:
        population = country_data.get("population", 0)
        region = country_data.get("region", "Unknown")
        currencies = ", ".join(country_data.get("currencies", {}).keys())

        print(f"\n=== Country Info ===")
        print(f"Region      : {region}")
        print(f"Population  : {population:,}")
        print(f"Currency    : {currencies}")

run_tool()


import json

def save_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

run_tool