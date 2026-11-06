# Loading data from a saved json file.

import json

with open("kenya_country.json", "r") as f:
    data = json.load(f)

print(data)