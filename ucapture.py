#!/usr/bin/python
"""\
Simple g-code streaming script
"""
import json
import time
import telnetlib
import argparse
import sys
import logging
import config

from pathlib import Path
from math import ceil
from time import sleep

from picamera2 import Picamera2, Preview
from libcamera import controls

from camera import Camera

from PIL import Image, ImageDraw
from io import BytesIO
from fractions import Fraction

from planner import Point, Objective, Plan, Margins

from tqdm import tqdm

def coords(s):
    try:
        x, y = map(float, s.split(','))
        return x, y
    except:
        raise argparse.ArgumentTypeError("Coordinates must be x,y")

logging.basicConfig(filename='logfile.txt', encoding='utf-8', level=logging.DEBUG)

parser = argparse.ArgumentParser(description='Capture images from a microscope')
parser.add_argument('--host', type=str, help='Host IP of FluidNC controller', default='10.64.0.180')
parser.add_argument('--end', type=coords, help="End coordinates", required=True)
parser.add_argument('--obj', type=str, help="ID of objective", required=True)
parser.add_argument('--vendor', type=str, help="Vendor of chip", required=True)
parser.add_argument('--chip', type=str, help="Identifier of chip", required=True)
parser.add_argument('--layer', type=str, help="ID of layer being imaged", required=True)
parser.add_argument('--overlap', type=int, help="Amount of overlap in procent", default=30)
parser.add_argument('--extraid', type=str, help="Extra identifier for run", default=None)
parser.add_argument('--format', type=str, help="Image output format", default='jpg')
parser.add_argument('--dry',  help="Dry run", action="store_true")
parser.add_argument('--out', type=str, help="Root output directory", default="out")
parser.add_argument('--view', help="Preview only", action="store_true")
parser.add_argument('--crop', help="Crop view", action="store_true")
parser.add_argument('--test', help="Test endpoints", action="store_true")
parser.add_argument('--level', help='Level the die', action="store_true")

args = parser.parse_args()
logging.info(args)

camera = Camera()

obj = config.OBJECTIVES[args.obj]
plan = Plan(obj, overlap=args.overlap/100, res=camera.get_capture_size())

logging.debug(f'Step_X: {plan.step_x}, Step_Y: {plan.step_y}')

x_pics = ceil((args.end[0] + plan.step_x/2) / plan.step_x)
y_pics = ceil((args.end[1] + plan.step_y/2) / plan.step_y)

print(f'Taking {x_pics}x{y_pics} pictures')
logging.info(f'Taking {x_pics}x{y_pics} pictures')

camera.add_overlay(obj=obj, overlap=args.overlap)

if args.view:
    while True:
        sleep(1)

print('Connecting to control board')
logging.info('Connecting to control board')
tn = telnetlib.Telnet()
tn.open(args.host, 23)
tn.write(b'\r\n')
tn.read_until(b'ok')
 
def cmd(data):
    logging.debug(f'cmd: Sending {type(data)} {data}')
    tn.write(str.encode(data + '\r\n'))
    tn.read_until(b'ok')

if not args.dry:
    logging.debug("Creating output dir")
    p = Path(args.out) / args.vendor / args.chip
    if args.extraid:
        p = p / args.extraid
    p.mkdir(parents=True, exist_ok=True)

logging.info('Homing')
cmd('G0 X0 Y0')
time.sleep(1)

if args.test:
    cmd('G0 X0 Y0')
    sleep(2)
    cmd(f'G0 X{plan.step_x * (x_pics-1)}')
    sleep(2)
    cmd(f'G0 Y{plan.step_y * (y_pics-1)}')
    while True:
        sleep(1)

if args.level:
    max_x = plan.step_x * (x_pics - 1)
    max_y = plan.step_y * (y_pics - 1)
    while True:
        cmd(f'G0 X{max_x} Y0')
        input()
        cmd(f'G0 X0 Y0')
        input()
        cmd(f'G0 X{max_x} Y{max_y}')
        input()

logging.info('Generating movement plan')
movement = []
for x in range(x_pics):
    for y in range(y_pics):
        movement.append([x,y_pics-y-1,x*plan.step_x, y*plan.step_y])

logging.debug(movement)

job = None

t = tqdm(total=x_pics * y_pics)
for move in movement:
    cmd(f'G0 X{move[2]} Y{move[3]}')
    if move[3] == 0.0:
        # New row, wait longer
        time.sleep(1.5)
    else:
        time.sleep(.5)
    t.update()
    if not args.dry:
        base_fn = f'r{move[1]:03d}_c{move[0]:03d}'
        fn = f'{base_fn}.{args.format}'
        camera.capture_still(str(p / fn))

t.close()
tn.close()
