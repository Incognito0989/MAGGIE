import requests
import json
from settings import *

TOKEN = None

def post(url, payload):
  headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': TOKEN
  }

  with open(payload, "r") as file:
    payload = json.load(file)

  response = requests.request("POST", url, headers=headers, json=payload, verify=False)
  print(response.text)

  if 'errors' in response.text:
    return 'error'

def process_service_for_ip(service_type, ip, service_dir):
    service_functions = {
        "Decode": post_decode_service,
        "Transcode": post_transcode_service,
        "Descramble": post_descramble_service
    }
    
    if service_type in service_functions:
        return service_functions[service_type](ip, service_dir)


def post_auth(base_ip):
    print(f"Getting authorization for {base_ip}")
    global TOKEN
    url = f"https://{base_ip}:8443/api/authenticate"

    payload = {
      "login": meg_login,
      "password": meg_password
    }
    headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    }

    try:
      response = requests.request("POST", url, headers=headers, json=payload, verify=False)
      TOKEN = response.json()['token']
      if TOKEN:
        print(f"SUCCESS, got token: {TOKEN}")
    except:
       print(f"Failed to get token for {base_ip}")

    if '"code": 401' in response.text:
       return 'error'
    return 'success'


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

    if 'errors' in response.text:
       return 'error'
    return 'success'

# TODO
def post_descramble_service(base_ip, payload):
  print(f"Posting descramble service to {base_ip} with payload: {payload}")
  url = f"https://{base_ip}:8443/api/v2/Descrambling?results=false"
  post(url, payload)

# TODO
def post_transcode_service(base_ip, payload):
   print(f"Posting transcode service to {base_ip} with payload: {payload}")
   url = f"https://{base_ip}:8443/api/v2/TranscodeServices?results=false"
   post(url, payload)