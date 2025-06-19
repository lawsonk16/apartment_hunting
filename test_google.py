import requests
import json


# Set up the API endpoint and parameters
endpoint = "https://api.openrouteservice.org/v2/directions/driving-car"
api_key = "Y5b3ce3597851110001cf62482287d1f6b5eb47a286dd6c756413ddb7" # Replace with your API key
start = "Berlin, Germany" # Replace with your starting address
end = "Hamburg, Germany" # Replace with your ending address

# Send a GET request to the API with the endpoint and parameters
params = {"api_key": api_key, "start": start, "end": end}
response = requests.get(endpoint, params=params)

# Parse the JSON response and extract the travel time
data = json.loads(response.text)
travel_time = data["features"][0]["properties"]["segments"][0]["duration"]

# Print the travel time in minutes
print("Travel time between {} and {} is {} minutes.".format(start, end, round(travel_time/60)))
