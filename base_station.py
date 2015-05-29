import urllib
import urllib2
import json
import time
import serial


# CONFIGURE CONSTANTS

IMAGE_TYPE           = '.jpg'
USER_IMAGE_PATH      = 'user_images/'
SATELLITE_IMAGE_PATH = 'satellite_images/'
SER                  = serial.Serial(port='/dev/tty.usbserial', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

# BASE STATION FUNCTIONS
#   - get image from web app
#   - send image to satellite

def get_image_from_web_app():
    request     = urllib2.Request('http://www.humanitiesatellite.com/api/v1/selfies/recent')
    response    = urllib2.urlopen(request).read()
    selfie      = json.loads(response)
    selfie_url  = selfie['picture']['feed']['url']

    user_id     = selfie['user_id']
    selfie_name = selfie['name'].lower().replace(' ', '_')
    timestamp   = int(time.time())

    selfie_file_name = '_'.join([str(user_id), selfie_name, str(timestamp)]) + IMAGE_TYPE

    import ipdb; ipdb.set_trace()

    path_to_image    = USER_IMAGE_PATH + selfie_file_name

    urllib.urlretrieve(selfie_url, path_to_image)
    return path_to_image

def send_image_to_satellite(path_to_image):
    print '   WAITING FOR SIGNAL FROM SATELLITE...'

    while True:
        line = SER.readline()
        if '<SEND_IMAGE>' in line:
            break

    print '   SENDING IMAGE TO SATELLITE...'

    with open(path_to_image, 'rb') as f:
        for line in f:
            if line[-1] != '\n':
                line = '%s\n' % line
            SER.write(line)
            SER.flush()
            time.sleep(0.1)

    SER.write('\n<END_IMAGE>\n')
    SER.flush()

def get_picture_from_satellite():

    print '   SENT SIGNAL TO SATELLITE...'

    SER.write('<SEND_IMAGE>\n')

    satellite_image_name = 'test.jpg'

    with open(SATELLITE_IMAGE_PATH + satellite_image_name, 'wb') as outfile:
        while True:
            line = SER.readline()
            time.sleep(0.1)
            if '<END_IMAGE>' in line:
                break
            outfile.write(line)
    return

print 'RUNNING get_image_from_web_app()'
path_to_image = get_image_from_web_app()

print 'RUNNING send_image_to_satellite()'
send_image_to_satellite(path_to_image)

print 'RUNNING get_picture_from_satellite()'
get_picture_from_satellite()

