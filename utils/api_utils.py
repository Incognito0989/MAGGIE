import requests
import json

TOKEN = None

def post_auth(base_ip):
    print(f"Getting authorization for {base_ip}")
    global TOKEN
    url = f"https://{base_ip}:8443/api/authenticate"

    payload = {
      "login": "syna",
      "password": "syna"
    }
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, json=payload, verify=False)
    TOKEN = response.json()['token']
    print(f"SUCCESS, got token: {TOKEN}")


def post_decode_service(base_ip, payload):
    print(f"Posting decode service to {base_ip} with payload: {payload}")
    url = f"https://{base_ip}:8443/api/v2/DecodeServices?results=false"
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': TOKEN
    }

    with open(payload, "r") as file:
      payload = json.load(file)

    response = requests.request("POST", url, headers=headers, json=payload, verify=False)
    print(response.text)

def post_descramble_service(base_ip, payload):
   print(f"Posting descramble service to {base_ip} with payload: {payload}")

def post_transcode_service(base_ip, payload):
   print(f"Posting transcode service to {base_ip} with payload: {payload}")