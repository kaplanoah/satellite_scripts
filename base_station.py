import urllib
import urllib2
import json
import time
import serial
import requests
import time


# CONFIGURE CONSTANTS

USE_DEV = True
USE_HARDWARE = True

IMAGE_TYPE           = '.jpg'
USER_IMAGE_PATH      = 'user_images/'
SATELLITE_IMAGE_PATH = 'satellite_images/'
GET_IMAGE_API_DEV    = 'http://localhost:3000/api/v1/selfies/recent'
GET_IMAGE_API_PROD   = 'http://www.humanitiesatellite.com/api/v1/selfies/recent'
SEND_IMAGE_API_DEV   = 'http://localhost:3000/selfies.json'
SEND_IMAGE_API_PROD  = 'http://www.humanitiesatellite.com/selfies.json'

if USE_HARDWARE:
    SER = serial.Serial(port='/dev/tty.usbserial', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)


# BASE STATION FUNCTIONS
#   - get image from web app
#   - send image to satellite

def get_image_from_web_app():
    api_url = GET_IMAGE_API_DEV if USE_DEV else GET_IMAGE_API_PROD

    request      = urllib2.Request(api_url)
    response_str = urllib2.urlopen(request).read()
    response     = json.loads(response_str)

    if response['status'] == 204:
        return None

    selfie = response['selfie']

    selfie_url  = selfie['picture']['feed']['url']
    user_id     = selfie['user_id']
    selfie_id   = selfie['id']

    image = Image(user_id, selfie_id)
    image_file_name = constuct_file_name(image)

    path_to_image = USER_IMAGE_PATH + image_file_name
    urllib.urlretrieve(selfie_url, path_to_image)

    return image

def send_image_to_satellite(image):
    print '   WAITING FOR SIGNAL FROM SATELLITE...'

    while True:
        line = SER.readline()
        if '<SEND_IMAGE>' in line:
            break

    print '   SENDING IMAGE TO SATELLITE...'

    with open(USER_IMAGE_PATH + image.earth_image_file_name, 'rb') as f:
        for line in f:
            if line[-1] != '\n':
                line = '%s\n' % line
            SER.write(line)
            SER.flush()
            time.sleep(0.1)

    SER.write('\n<END_IMAGE>\n')
    SER.flush()

def get_picture_from_satellite(image):

    print '   SENT SIGNAL TO SATELLITE...'

    SER.write('<SEND_IMAGE>\n')

    with open(SATELLITE_IMAGE_PATH + image.space_image_file_name, 'wb') as outfile:
        while True:
            line = SER.readline()
            time.sleep(0.1)
            if '<END_IMAGE>' in line:
                break
            outfile.write(line)
    return

def send_picture_to_app(image):
    api_url = SEND_IMAGE_API_DEV if USE_DEV else SEND_IMAGE_API_PROD
    files = {'file': open(SATELLITE_IMAGE_PATH + image.space_image_file_name, 'rb')}

    r = requests.post(api_url, {'name': image.space_image_file_name}, files=files)

    print r.text


# HELPER FUNCTIONS

def constuct_file_name(image, is_in_space=False):
    timestamp = int(time.time())

    image_info = [str(image.user_id), str(image.earth_image_id), str(timestamp)]
    if is_in_space: image_info.append('space')

    return '_'.join(image_info) + IMAGE_TYPE


class Image:
    def __init__(self, user_id, earth_image_id):
        self.user_id = user_id
        self.earth_image_id = earth_image_id
        self.earth_image_file_name = constuct_file_name(self)
        self.space_image_file_name = constuct_file_name(self, True)


# EXECUTE

def full_cycle():

    print 'RUNNING get_image_from_web_app()'
    image = get_image_from_web_app()

    if image and USE_HARDWARE:

        print 'RUNNING send_image_to_satellite()'
        send_image_to_satellite(image)

        print 'RUNNING get_picture_from_satellite()'
        get_picture_from_satellite(image)

        print 'RUNNING send_picture_to_app()'
        send_picture_to_app(image)

while True:
    full_cycle()
    time.sleep(5)
