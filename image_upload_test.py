import requests
import time

url   = 'http://localhost:3000/selfies.json'
files = {'file': open('satellite_images/test.jpg', 'rb')}

user_id     = 1
selfie_name = 'image_from_satellite'
timestamp   = int(time.time())

selfie_file_name = '_'.join([str(user_id), selfie_name, str(timestamp)]) + '.jpg'

r = requests.post(url, {'name': selfie_file_name}, files=files)

text = r.text

print text