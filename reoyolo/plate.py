import json
from operator import le
import os
from tokenize import Token
import requests

KNOWN_PEOPLE = os.environ.get("REOYOLO_PLATE_PEOPLE", '{}')
KNOWN_PEOPLE = json.loads(KNOWN_PEOPLE)

# https://docs.platerecognizer.com/?python#countries
REGION = [os.environ.get("REOYOLO_PLATE_REGION", "us")]
TOKEN = os.environ.get("REOYOLO_PLATE_TOKEN", None)

def process(img):
    if TOKEN is None:
        return "No token."
    return_str = "No car detected?"
    with open(img, 'rb') as fp:
        response = requests.post(
                    'https://api.platerecognizer.com/v1/plate-reader/',
                    data=dict(regions=REGION), 
                    files=dict(upload=fp),
                    headers={'Authorization': f'Token {TOKEN}'})
        response.raise_for_status()
        resp = response.json()
        
        if "results" in resp:
            people = set()
            for car in resp['results']:
                plate = car.get('plate', None)
                if plate:
                    known_person = KNOWN_PEOPLE.get(plate, f"Unknown's:{plate}")
                    people.add(known_person)
            if len(people) == 1:
                return_str = f"It's {people.pop()} car"
            elif len(people) > 1:
                return_str = f"It's {people} car"
    return return_str

