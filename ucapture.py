#!/usr/bin/python
"""\
Simple g-code streaming script
"""
import json
# import serial
import time
import telnetlib
import argparse
import sys
from pathlib import Path

from math import ceil
from time import sleep

from picamera import PiCamera
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


parser = argparse.ArgumentParser(description='Run my amscope')
parser.add_argument('--host', type=str, help='Host IP of GRBL-ESP32 controller', default='10.64.0.180')
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

# print(args)

margin = Margins(top=0.17, left=0.20, bottom=0.23, right=0.20)
small_margin = Margins(top=0.05, left=0.05, bottom=0.05, right=0.05)
no_margin = Margins(top=0, left=0, bottom=0, right=0)

#OBJECTIVES = {
#    'am5x':  Objective(2.6, 1.9, small_margin),
#    'am10x': Objective(1.3, 1.0, small_margin),
#    'am50x': Objective(0.26, 0.2, small_margin),
#    'ol20x': Objective(0.65, 0.49, small_margin)
#}

OBJECTIVES = {
    'ol5x': Objective(1.7, 1.3, small_margin),
    'ol10x': Objective(0.9, 0.65, small_margin),
    'ol20x': Objective(0.44, 0.34, small_margin)
}

CAMERA_RES = Point(4056, 3040)

obj = OBJECTIVES[args.obj]
plan = Plan(obj, overlap=args.overlap/100, res=CAMERA_RES)

print(f'Step_X: {plan.step_x}, Step_Y: {plan.step_y}')

x_pics = ceil((args.end[0] + plan.step_x/2) / plan.step_x)
y_pics = ceil((args.end[1] + plan.step_y/2) / plan.step_y)

print(f'Taking {x_pics}x{y_pics} pictures')

overlay = plan.get_overlay(4)

camera = PiCamera()
camera.resolution = CAMERA_RES.scaled(1)
print(f'Camera res: {CAMERA_RES.scaled(1)}')
camera.start_preview(resolution=CAMERA_RES.scaled(4))
if args.crop:
    camera.zoom = (margin.top, margin.left, 1-margin.left-margin.right, 1-margin.top-margin.bottom)

o = camera.add_overlay(overlay.tobytes(), size=overlay.size)
o.alpha = 32
o.layer = 3

# time.sleep(5)

# sys.exit()

if args.view:
    while True:
        sleep(1)

# Open serial port
#s = serial.Serial('/dev/ttyUSB0',115200)
#print('Opening Serial Port')

print('Connecting to control board')
tn = telnetlib.Telnet()
tn.open(args.host, 23)
tn.write(b'\r\n')
tn.read_until(b'ok')
 
# Wake up 
#s.write(b"\r\n\r\n") # Hit enter a few times to wake the Printrbot
#time.sleep(2)   # Wait for Printrbot to initialize
#s.flushInput()  # Flush startup text in serial input


def cmd(data):
    # print(f'cmd: Sending {type(data)} {data}')
    #s.write(str.encode(data) + b'\n')
    #res = s.readline()
    tn.write(str.encode(data + '\r\n'))
    tn.read_until(b'ok')
    #print(f'cmd: Result: {str(res.strip())}')

if not args.dry:
    print("Creating output dir")
    p = Path(args.out) / args.vendor / args.chip
    if args.extraid:
        p = p / args.extraid
    p.mkdir(parents=True, exist_ok=True)

#    print("Writing parameters file")
#    with open(p / 'parameters.json', 'w') as json_file:
#        print(vars(args))
#        json.dump(vars(args), json_file, indent=4)

print("Calibrating camera")
cmd('G90')
cmd('G0 X1 Y1')
camera.iso = 100
# Wait for the automatic gain control to settle
sleep(2)
# Now fix the values
camera.shutter_speed = camera.exposure_speed
camera.exposure_mode = 'off'
g = camera.awb_gains
camera.awb_mode = 'off'
#camera.awb_gains = g
camera.awb_gains = (Fraction(493, 256), Fraction(193, 64))

print('Homing')
#cmd('G0 X0 Y-0.5')
#sleep(1)
cmd('G0 X0 Y0')
time.sleep(2)

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

print('Generating movement plan')
movement = []
for x in range(x_pics):
    for y in range(y_pics):
        movement.append([x,y_pics-y-1,x*plan.step_x, y*plan.step_y])

#print(movement)

t = tqdm(total=x_pics * y_pics)
for move in movement:
    cmd(f'G0 X{move[2]} Y{move[3]}')
    time.sleep(3)
    t.update()
    if not args.dry:
        base_fn = f'r{move[1]:03d}_c{move[0]:03d}'
        if args.format == 'jpg':
            fn = f'{base_fn}.jpg'
            camera.capture(str(p / fn))
            time.sleep(0.5)
        elif args.format == "png":
            fn = f'{base_fn}.png'
            camera.capture(str(p / fn))
            time.sleep(0.5)
        elif args.format == 'crop':
            fn = f'{base_fn}.png'
            stream = BytesIO()
            camera.capture(stream, format="png")
            stream.seek(0)
            image = Image.open(stream)
            im_out = image.crop(plan.crop)
            im_out.save(str(p / fn))


t.close()
tn.close()

sys.exit()

for y in range(y_pics):
    cmd('G91')
    for x in range(x_pics):
        stream = BytesIO()
        #cmd(f'G0 X{x * step_x_size}')
        #fn = f'c{x:03d}_r{step_y-1-y:03d}.jpg'
        fn = f'r{y_pics-1-y:03d}_c{x:03d}.jpg'
        # print(f'Taking picture {fn}')
        t.update()
        if not args.dry:
            #camera.capture(stream, format="jpeg")
            camera.capture(str(p / fn))
            #stream.seek(0)
            #image = Image.open(stream)
            #im_out = image.crop(plan.crop)
            #im_out.save(str(p / fn), compress_level=0)
            time.sleep(0.5)
        cmd(f'G0 X{plan.step_x}')
        time.sleep(1)
    cmd(f'G0 Y{plan.step_y}')
    cmd('G90 G0 X0')
    #cmd(f'G0 X0 Y{(y+1) * step_y_size}')
    time.sleep(2)

#s.close()
t.close()
tn.close()
