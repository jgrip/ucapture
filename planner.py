from dataclasses import dataclass
from typing import List
from collections import namedtuple 

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
        overlap = self.obj.move_x * self.overlap
        step_x = round(self.obj.move_x - overlap, 2)
        return step_x

    @property
    def step_y(self):
        overlap = self.obj.move_y * self.overlap
        return round(self.obj.move_y - overlap, 2)
