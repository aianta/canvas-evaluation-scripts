'''
A python script meant to pull traces from an application registered on a log ui server, in a format 
that allows them to be run through evaluation_script.py.

Logic:

1. Download all traces associated with a LogUI application. 
2. Rename the trace files to match corresponding task instance id's.
'''

import requests
import csv
import os.path

LOGUI_SERVER_HOST="https://localhost:8000"
LOGUI_APPLICATION_ID="b50caafb-8f44-45b3-9630-727c85bd0ace"
LOGUI_USER=""
LOGUI_PASSWORD=""
OUTPUT_DIR="./trajectories/"
MAPPING_FILE="odox-6d-mapping.csv"

def get_jwt_token(user, password):

    request_body = {
        "username": user,
        "password": password
    }

    response = requests.post(LOGUI_SERVER_HOST + "/api/user/auth/", data=request_body, verify=False)

    auth_data = response.json()

    return auth_data["token"]


def get_application_flights(jwt_token, application_id):

    headers = {"Authorization": f"jwt {jwt_token}"}
    response = requests.get(LOGUI_SERVER_HOST+f"/api/flight/list/{application_id}", headers=headers, verify=False)
    response = response.json()

    return [x["id"] for x in response]


def download_logs(jwt_token, flight_ids, mappings):

    headers = {"Authorization": f"jwt {jwt_token}"}

    for flight_id in flight_ids:
        print(f"Finding mapping for flight id {flight_id}...")

        try:
            task_instance_id = mappings[flight_id]

            
            print(f"Flight id {flight_id} maps to task_instance_id: {task_instance_id}")

            output_file_name = f"{OUTPUT_DIR}{task_instance_id}"

            if(os.path.isfile(output_file_name + ".json")):
                output_file_name += "-alt.json"
            else:
                output_file_name += ".json"

            print(f"Downloading {output_file_name}")
            response = requests.get(LOGUI_SERVER_HOST+f"/api/flight/download/{flight_id}/", verify=False, headers=headers)
            with open(f"{output_file_name}", "wb") as out_file:
                out_file.write(response.content)
        except KeyError:
            print(f"Unknown task instance id for flight_id: {flight_id}")

def get_mapping_to_task_instances(mapping_file_path):
    result={}
    with open(mapping_file_path, 'r') as mapping_file:
        reader = csv.reader(mapping_file, delimiter="," )
        line_count = 0
        for row in reader:
            if line_count == 0:
                line_count += 1
                continue
            else:
                # result[flight_id] = task_instance id
                result[row[1]] = row[0]
    
    return result


print(f"Getting task instance mappings from {MAPPING_FILE}")
flight_id_to_task_instance_mappings = get_mapping_to_task_instances(MAPPING_FILE)

print(f"Getting JWT token")
jwt_token = get_jwt_token(LOGUI_USER, LOGUI_PASSWORD)

print(f"Got JWT token, fetching flights IDs associated with application {LOGUI_APPLICATION_ID}")
flight_ids = get_application_flights(jwt_token, LOGUI_APPLICATION_ID)

print(f"Got {len(flight_ids)} flights for application {LOGUI_APPLICATION_ID}, downloading into logs folder...")
download_logs(jwt_token, flight_ids, flight_id_to_task_instance_mappings)

