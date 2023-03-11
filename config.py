from planner import Objective, Margins

exposure = 9994
analogue_gain = 1.74
colour_gain = (2.25, 2.63)

CAPTURE = {
    'ExposureTime': exposure,
    'AnalogueGain': analogue_gain,
    # 'ColourGains': colour_gain,
    'AeEnable': False,
    # "AwbEnable": False,
}   

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
    'ol5x': Objective(1.7, 1.3, no_margin),
    'ol10x': Objective(0.9, 0.65, no_margin),
    'ol20x': Objective(0.44, 0.34, no_margin)
}

# Resolution of the monitor used for preview
MONITOR = (1920, 1080)