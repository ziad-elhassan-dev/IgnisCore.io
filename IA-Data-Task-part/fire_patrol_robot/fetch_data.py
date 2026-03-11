import requests
import time
import json

base_url = "https://yboost.corentinhoffmann.fr/"
token = "x"

headers = {"Authorization": f"Bearer {token}"}
data = []

def fetch_data(output_file="sensor_data.json", interval=0.5):
    data = []
    while True:
        response = requests.get(f"{base_url}/api/message", headers=headers)
        print(response.status_code)

        frame = response.json()
        print(frame)

        data.append(frame)

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        time.sleep(interval)
        
if __name__ == "__main__":
    fetch_data()