import requests

r = requests.get("https://beamtic.com/api/request-headers")

print(r.text)