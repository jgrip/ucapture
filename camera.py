from picamera2 import Picamera2, Preview
from libcamera import controls

from planner import Point

from PIL import Image, ImageDraw

import tempfile
import cv2
import logging

import config

class Camera(object):
    def __init__(self):
        self.cam = Picamera2()

        self.capture = self.cam.create_still_configuration()
        self.capture_x = self.capture['main']['size'][0]
        self.capture_y = self.capture['main']['size'][1]
        self.preview_scale = 4
        # self.preview_x = (((self.capture_x // self.preview_scale) + 31) // 32) * 32
        # self.preview_y = (((self.capture_y // self.preview_scale) + 15) // 16) * 16
        logging.debug(f'Sensor size: {self.capture_x} x {self.capture_y}')

        self.preview_x = int(self.capture_x * (config.MONITOR[1] / self.capture_y))
        self.preview_y = config.MONITOR[1]
        logging.debug(f'Preview size: {self.preview_x} x {self.preview_y}')
        self.preview = self.cam.create_still_configuration(lores={'size': (self.preview_x, self.preview_y)}, display='lores', controls = config.CAPTURE)

        offset_x = (config.MONITOR[0] - self.preview_x) // 2
        offset_y = (config.MONITOR[1] - self.preview_y) // 2
        self.cam.start_preview(Preview.DRM,
                               x=offset_x,
                               y=offset_y,
                               width=self.preview_x,
                               height=self.preview_y)

        self.cam.configure(self.preview)
        self.cam.start()

    def get_capture_size(self):
        return Point(self.capture_x, self.capture_y)

    def get_preview_size(self):
        return Point(self.preview_x, self.preview_y)

    def add_overlay(self, obj, overlap):
        img = Image.new('RGBA', (self.preview_x, self.preview_y))
        draw = ImageDraw.Draw(img)

        crop_top = int(self.preview_y * obj.margins.top)
        crop_bot = int(self.preview_y - (self.preview_y * obj.margins.bottom))
        crop_left = int(self.preview_x * obj.margins.left)
        crop_right = int(self.preview_x - (self.preview_x * obj.margins.right))

        over_top = int(crop_top + (self.preview_y * overlap/2/100))
        over_bot = int(crop_bot - (self.preview_y * overlap/2/100))
        over_left = int(crop_left + (self.preview_x * overlap/2/100))
        over_right = int(crop_right - (self.preview_x * overlap/2/100))

        mid_x = (self.preview_x // 2) - 1
        mid_y = (self.preview_y // 2) - 1

        logging.debug(f'Crop: {crop_top}x{crop_left} - {crop_right}x{crop_bot}')
        logging.debug(f'Over: {over_top}x{over_left} - {over_right}x{over_bot}')

        draw.rectangle((crop_left, crop_top, crop_right, crop_bot),(255,255,255,0),(255,0,0),10)
        draw.rectangle((over_left, over_top, over_right, over_bot),(255,255,255,0),(0,255,0),10)
        draw.rectangle((mid_x, 0, mid_x, self.preview_y), (255,255,255,0), (0,0,255), 2)
        draw.rectangle((0, mid_y, self.preview_x, mid_y), (255,255,255,0), (0,0,255), 2)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            print(img)
            img.save(tmpdir + '/img.png')
            overlay = cv2.imread(tmpdir + '/img.png', cv2.IMREAD_UNCHANGED)
            self.cam.set_overlay(overlay)

    def capture_still(self, filepath):
        self.cam.capture_file(filepath, wait=False)
        meta = self.cam.capture_metadata()
        logging.info(f'Captured {filepath}: {meta}')

    def wait(self, job):
        self.cam.wait(job)
