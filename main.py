import requests

# Your API Key
API_KEY = "dc98474508c65500e4a8776d96a76a5e"
BASE_HOST = "v3.football.api-sports.io" # As specified in x-rapidapi-host

url = f"https://{BASE_HOST}/leagues"

payload = {} # No payload needed for GET requests to this endpoint
headers = {
  'x-rapidapi-key': API_KEY,
  'x-rapidapi-host': BASE_HOST
}

try:
    response = requests.request("GET", url, headers=headers, data=payload)
    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

    # Print the raw JSON response
    print(response.text)

    # You can also parse it to JSON to work with the data
    data = response.json()
    if data and data['response']:
        print("\n--- Parsed League Names ---")
        for league in data['response']:
            print(f"League Name: {league['league']['name']}, Country: {league['country']['name']}")
    else:
        print("No leagues found or unexpected API response structure.")

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    print(f"Response content: {response.text}")
except requests.exceptions.RequestException as req_err:
    print(f"An error occurred: {req_err}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
