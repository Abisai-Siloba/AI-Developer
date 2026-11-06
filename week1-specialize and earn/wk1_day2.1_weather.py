import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("RESTCOUNTRIES_API_KEY")
if not api_key:
    raise ValueError("RESTCOUNTRIES_API_KEY is not set in the environment or .env file.")

url = "https://api.restcountries.com/countries/v5/names.common/Chaina?pretty=1"
request_headers = {
    "Authorization": f"Bearer {api_key}"
}

response = requests.get(url, headers=request_headers, timeout=15)
print("Status code:", response.status_code)
response.raise_for_status()
data = response.json()

print("-"*130)
print(data)
print("="*130)

print("Country Information:")   
print("-"*130)

#print("Country Name:", data["object"]["name"]["official"])

print("="*130)


import json
def save_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Data saved to {filename}")


if data:
    save_to_file(data, "Chaina_country.json")
