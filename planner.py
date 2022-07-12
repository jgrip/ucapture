from dataclasses import dataclass
from typing import List
from collections import namedtuple 
from PIL import Image, ImageDraw

Margins = namedtuple('Margins', ['top', 'bottom', 'left', 'right'])

@dataclass
class Point:
    x: float
    y: float

    def scaled(self, scale):
        return (int(self.x/scale), int(self.y/scale))

@dataclass
class Objective:
    width: float
    height: float
    margins: Margins

    @property
    def move_x(self) -> float:
        return round(self.width - (self.margins.left * self.width) - (self.margins.right * self.width), 2)

    @property
    def move_y(self) -> float:
        return round(self.height - (self.margins.top * self.height) - (self.margins.bottom * self.height), 2)


class Plan:
    def __init__(self, objective, overlap=0.3, res=Point):
        self.obj = objective
        self.overlap = overlap
        self.res = res

    @property
    def step_x(self):
        # print(f'step_x: obj width {self.obj.width}')
        # print(f'step_x: obj move  {self.obj.move_x}')
        overlap = self.obj.move_x * self.overlap
        step_x = round(self.obj.move_x - overlap, 2)
        # print(f'step_x:     move  {step_x}')
        return step_x

    @property
    def step_y(self):
        overlap = self.obj.move_y * self.overlap
        return round(self.obj.move_y - overlap, 2)

    @property
    def crop(self):
        crop_top = int(self.res.y * self.obj.margins.top)
        crop_bot = int(self.res.y - (self.res.y * self.obj.margins.bottom))
        crop_left = int(self.res.x * self.obj.margins.left)
        crop_right = int(self.res.x - (self.res.x * self.obj.margins.right))

        return (crop_left, crop_top, crop_right, crop_bot)


    def get_overlay(self, scale):
        img = Image.new('RGB', (self.res.x, self.res.y))
        draw = ImageDraw.Draw(img)
        
        crop_top = int(self.res.y * self.obj.margins.top)
        crop_bot = int(self.res.y - (self.res.y * self.obj.margins.bottom))
        crop_left = int(self.res.x * self.obj.margins.left)
        crop_right = int(self.res.x - (self.res.x * self.obj.margins.right))

        over_top = int(crop_top + (self.res.y * self.overlap/2))
        over_bot = int(crop_bot - (self.res.y * self.overlap/2))
        over_left = int(crop_left + (self.res.x * self.overlap/2))
        over_right = int(crop_right - (self.res.x * self.overlap/2))

        # print(f'Top: crop {crop_top}, over {over_top}')
        # print(f'Bot: crop {crop_bot}, over {over_bot}')
        # print(f'Top: crop {crop_left}, over {over_left}')
        # print(f'Bot: crop {crop_right}, over {over_right}')

        draw.rectangle((crop_left, crop_top, crop_right, crop_bot),(255,255,255,0),(255,0,0),20)
        # draw.rectangle((crop_left, crop_top, over_left, crop_bot),(255,255,0,0))
        # draw.rectangle((over_right, crop_top, crop_right, crop_bot),(255,255,0,0))
        # draw.rectangle((crop_left, crop_top, crop_right, over_top),(255,255,0,0))
        # draw.rectangle((crop_left, over_bot, crop_right, crop_bot),(255,255,0,0))
        draw.rectangle((over_left, over_top, over_right,over_bot), outline=(0,255,0,0), width=20)
        
        print(f'Image: {img}')

        img_res = img.resize((int(self.res.x/scale), int(self.res.y/scale)))
        print(f'Scale: {img_res}')
        pad = Image.new('RGB', (
            ((img_res.size[0] + 31) // 32) * 32,
            ((img_res.size[1] + 15) // 16) * 16,
        ))
        pad.paste(img_res, (0, 0))

        print(f'  Pad: {pad}')

        print(f' Crop: {crop_right-crop_left}x{crop_bot-crop_top}+{crop_left}+{crop_top}')

        return pad
