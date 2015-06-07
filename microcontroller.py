import picamera
import pygame
from time import sleep
import serial
import sys


# CONFIGURE CONSTANTS

IMAGE_DIRECTORY      = 'Desktop/images/'
IMAGE_TYPE           = '.jpg'
USER_IMAGE_PATH      = IMAGE_DIRECTORY + 'user_image'      + IMAGE_TYPE
SATELLITE_IMAGE_PATH = IMAGE_DIRECTORY + 'satellite_image' + IMAGE_TYPE
IMAGE_DISPLAY_TIME   = 4   # seconds
IMAGE_QUALITY        = 0.5 # 0-1 where 1 is best resultion
SER                  = serial.Serial(port='/dev/ttyAMA0', baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)

# IMAGE DISPLAY CLASS
#   - initialize pygame
#   - scale and center images
#   - display images

class ImageDisplay:
    screen = None;
    screen_height = 0;
    screen_width = 0;
    
    def __init__(self):
        try:
            pygame.display.init()
        except:
            print "Unable to initialize frame buffer!"
            sys.exit()

        self.screen_height = pygame.display.Info().current_h
        self.screen_width = pygame.display.Info().current_w
        
        self.screen = pygame.display.set_mode([self.screen_width, self.screen_height], pygame.FULLSCREEN)
        self.screen.fill([0, 0, 0])        

        # This hides the mouse pointer which is unwanted in this application
        pygame.mouse.set_visible(False)
        pygame.display.update()

    def displayImage(self, filename, sleep_time):
        img = pygame.image.load(filename)

        img_height = img.get_height()
        img_width = img.get_width()

        # if the image isn't the same size as the screen, scale it
        if ((img_height != self.screen_height) or (img_width != self.screen_width)):
            # determine the image's height if it fills the whole width
            scaled_height = int((float(self.screen_width) / img_width) * img_height)

            # if the scaled image would be taller than the screen, limit the height and scale the width
            if (scaled_height > self.screen_height):
                scaled_height = self.screen_height
                scaled_width = int((float(self.screen_height) / img_height) * img_width)
            else:
                scaled_width = self.screen_width

            img_bitsize = img.get_bitsize()

            # transform.smoothscale() can only be used for 24-bit and 32-bit images. If this is not a 24-bit or 32-bit
            # image, use transform.scale() instead which will be ugly but at least will work
            if (img_bitsize == 24 or img_bitsize == 32):
                img = pygame.transform.smoothscale(img, [scaled_width, scaled_height])
            else:
                img = pygame.transform.scale(img, [scaled_width, scaled_height])

            # find where to place the image so it will be centered
            display_x = (self.screen_width - scaled_width) / 2
            display_y = (self.screen_height - scaled_height) / 2
        else:
            # no scaling was applied so image is already full-screen
            display_x = 0
            display_y = 0

        # blank screen before showing photo in case it doesn't fill the whole screen
        self.screen.fill([0, 0, 0])
        self.screen.blit(img, [display_x, display_y])
        pygame.display.update()
        sleep(sleep_time)
        pygame.display.quit()


# MICROCONTROLLER FUNCTIONS
#   - get image from base station
#   - display image on screen
#   - take picture
#   - send picture to base station

def get_image_from_base_station():
    
    SER.write('<SEND_IMAGE>\n')

    with open(USER_IMAGE_PATH, 'wb') as outfile:
        while True:
            line = SER.readline()
            sleep(0.1)
            if '<END_IMAGE>' in line:
                break
            outfile.write(line)

    SER.flush()
    return

def display_image_on_screen():
    player = ImageDisplay()
    print USER_IMAGE_PATH
    player.displayImage(USER_IMAGE_PATH, IMAGE_DISPLAY_TIME)
    # sleep(IMAGE_DISPLAY_TIME)
    return

def take_picture(send_to_base_station):
    with picamera.PiCamera() as camera:
        camera.resolution = (int(2592 * IMAGE_QUALITY), int(1944 * IMAGE_QUALITY))
        sleep(2)
        camera.capture(SATELLITE_IMAGE_PATH)
    
    if send_to_base_station:
        print 'RUNNING send_picture_to_base_station()'
        send_picture_to_base_station()

def send_picture_to_base_station():
    print '   WAITING FOR SIGNAL FROM BASE STATION...'

    while True:
        line = SER.readline()
        if '<SEND_IMAGE>' in line:
            break

    print '   SENDING IMAGE TO BASE STATION...'

    with open(SATELLITE_IMAGE_PATH, 'rb') as f:
        for line in f:
            if line[-1] != '\n':
                line = '%s\n' % line
            SER.write(line)
            SER.flush()
            sleep(0.1)

    SER.write('\n<END_IMAGE>\n')
    SER.flush()


send_to_base_station = True

print 'RUNNING get_image_from_base_station()'
get_image_from_base_station()

print 'RUNNING display_image_on_screen()'
display_image_on_screen()

print 'RUNNING take_picture()'
take_picture(send_to_base_station)
