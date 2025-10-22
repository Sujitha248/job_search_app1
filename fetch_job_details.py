import requests
import json

# 🔑 Replace this with your actual API key
API_KEY = "rEabbc4ElMakoLp2INsVxDOgdPSAYGB6"
job_id = 314351456

# 🟢 API endpoint to collect full job details
url = f"https://api.coresignal.com/cdapi/v2/job_base/collect/{job_id}"

# 🧾 Request headers with API key
headers = {
    "apikey": rEabbc4ElMakoLp2INsVxDOgdPSAYGB6
}

# 📡 Send the GET request
response = requests.get(url, headers=headers)

# ✅ Process the response
if response.status_code == 200:
    job_data = response.json()
    print("\n✅ Full Job Data Retrieved:\n")
    print(json.dumps(job_data, indent=4))
else:
    print("❌ Failed to fetch job data:", response.status_code)
    print(response.text)