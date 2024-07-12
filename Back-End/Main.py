import requests
from Apis.BackendTrabajoDomestico import app


def fetch_data():
    url = "http://localhost:5000/get_data"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

    data = fetch_data('get_data')
    if data:
        print(data)
