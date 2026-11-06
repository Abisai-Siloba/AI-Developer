import requests

url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true"

response = requests.get(url)
response.raise_for_status()
payload = response.json()

print("Status code:", response.status_code)
print()

print("Data received:", payload)
print()

print("Current Weather:")
print("Temperature:", payload["current_weather"]["temperature"], "°C")
print("Wind Speed:", payload["current_weather"]["windspeed"], "km/h")
print("="*100)

#url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
response = requests.get(url)
response.raise_for_status()
payload = response.json()

print("Status code:", response.status_code)
print()

print("Data received:", payload)
print()

print("Bitcoin Price:")
print("USD:", payload["bitcoin"]["usd"], "$")
print("="*100)
