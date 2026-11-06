import requests

country_code = "KEN"  # Replace with the desired country code
url = f"https://api.worldbank.org/v2/country/{country_code}?format=json"

response = requests.get(url)
response.raise_for_status()

payload = response.json()
country = payload[1][0]

print("Status code:", response.status_code)
print()

print("Data received:", country)
print()

print("Country:", country["name"])
print("Capital:", country["capitalCity"])
print("Region:", country["region"]["value"])
print("Income Level:", country["incomeLevel"]["value"])