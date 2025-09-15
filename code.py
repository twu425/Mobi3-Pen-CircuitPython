# code.py
# Note: Units of measurement are in millimeters, units of rotation are in radians
import usb_hid
import time
import board
import busio
import bitbangio
import math
import digitalio
from adafruit_hid.mouse import Mouse
from moving_average import MovingAverage
from as5600 import AS5600

print("Hello World!")

# Setup HID devices
custom = usb_hid.devices[-1] # The custom HID device is the last in the list from usb_hid.enable() in boot.py
mouse = Mouse(usb_hid.devices)

# Function to send a report using our custom HID device
# TODO: Refactor custom HID device into it's own class
def send_report(x=0, y=0, z=0, buttons=0):
    # x and y must be signed bytes (-127 to 127)
    x_byte = x & 0xFF
    y_byte = y & 0xFF
    z_byte = z & 0xFF
    buttons_byte = buttons & 0xFF
    # The report's report ID is added automatically by the library, so it should be omitted
    report = bytes([x_byte, y_byte, z_byte, buttons_byte])
    # print(report)
    custom.send_report(report)

# Setup 3 I2C busses to handle the three as5600 sensors. They must be on seperate busses as they all use the same slave address.
# i2c1 corresponds to rotation_sensor_3 (the turntable one) and not arm1's rotation sensor. Sorry!
i2c1 = busio.I2C(scl=board.GP1, sda=board.GP0, frequency=100000)
i2c2 = busio.I2C(scl=board.GP7, sda=board.GP6, frequency=100000) 
i2c3 = bitbangio.I2C(scl=board.GP9, sda=board.GP8, frequency=100000) # The pi pico only has 2 hardware i2c busses, so a third one is bit-banged onto GPIO 8 and 9

rotation_sensor_1 = AS5600(i2c2) # Arm 1 rotation sensor
rotation_sensor_2 = AS5600(i2c3) # Arm 2 rotation sensor
rotation_sensor_3 = AS5600(i2c1) # Turntable rotation sensor

def determine_pos(l1, l2, offset, rotation_1, rotation_2, rotation_3):
    """
    :param l1: Length of arm 1 (mm)
    :param l2: Length of arm 2 (mm)
    :param rotation_1: Rotation of arm 1 (radians)
    :param rotation_2: Rotation of arm 2 (radians)
    :param rotation_3: Turntable rotation (radians)
    :return: A tuple containing the x, y, and z coordinates of the endpoint
    """
        
    # Determine the position of the start of the first arm
    x1 = (math.sin(rotation_1) * l1) + offset
    y1 = 0
    z1 = math.cos(rotation_1) * l1
    #print(x1, y1, z1)
    
    # Determine the position of the start of the second arm 
    x2 = x1 + math.sin(rotation_2 + rotation_1) * l2
    y2 = y1 
    z2 = z1 + math.cos(rotation_2 + rotation_1) * l2
    #print(x2, y2, z2)
    
    # Determine the position of the pen-point
    x3 = (x2 * math.cos(rotation_3)) - (y2 * math.sin(rotation_3))
    y3 = (x2 * math.sin(rotation_3)) - (y2 * math.cos(rotation_3))
    z3 = z2
    
    return (x3, y3, z3)
    
    
def determine_height(l1, l2, rotation_1, rotation_2):
    """
    :param l1: Length of arm 1
    :param l2: Length of arm 2
    :param rotation_1: Rotation of arm 1
    :param rotation_2: Rotation of arm 2
    :return: Z-position of the end point
    """
    rotation_1 = math.radians(rotation_1)
    rotation_2 = math.radians(rotation_2)


    z = (math.cos(rotation_1) * l1) + (math.cos(rotation_1 + rotation_2) * l2)

    return z




# All measures are in millimeters
arm1_length = 170
arm2_length = 205
offset = 0

# Coordinates
x = 0
y = 0
z = 0

# Previous coordinates
previous_x = x
previous_y = y
previous_z = z

# Accumulation
# TODO: Explain this
accumulation_x = 0
accumulation_y = 0
accumulation_z = 0

# Move
move_x = 0
move_y = 0
move_z = 0

sensitivity = 10
mouse_smoothing_count = 3 # Determines how many of the last N mouse coordinates to average out for smoother movement
threshold = 2.0  # Ignore movements less than this

arm1_rotation_moving_average = MovingAverage(size=mouse_smoothing_count)
arm2_rotation_moving_average = MovingAverage(size=mouse_smoothing_count)
turntable_rotation_moving_average = MovingAverage(size=mouse_smoothing_count)

# Offsets
arm1_rotation_offset = 360-286 # Arm 1
arm2_rotation_offset = 360-111 # Arm 2
turntable_rotation_offset = 360-0 # Turntable
# def callibrate(arm1_raw_rotation, arm2_raw_rotation, turntable_raw_rotation):
#     arm1_rotation_offset = (2 * math.pi) - arm1_raw_rotation
#     arm2_rotation_offset = (2 * math.pi) - arm2_raw_rotation
#     turntable_rotation_offset = (2 * math.pi) - turntable_raw_rotation
##############
## Buttons
##############

m1_pin = board.GP11
m2_pin = board.GP12
m3_pin = board.GP13

def registerButton(button_pin):
    button = digitalio.DigitalInOut(button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    return button

m1_btn = registerButton(m1_pin)
m2_btn = registerButton(m2_pin)
m3_btn = registerButton(m3_pin)

##########
## Loop
##########

while True:
        
    arm1_raw_rotation = ((rotation_sensor_1.angle / 4096) * 2 * math.pi + math.radians(arm1_rotation_offset)) % (2 * math.pi)
    arm2_raw_rotation = ((rotation_sensor_2.angle / 4096) * 2 * math.pi + math.radians(arm2_rotation_offset)) % (2 * math.pi)
    arm3_raw_rotation = ((rotation_sensor_3.angle / 4096) * 2 * math.pi + math.radians(turntable_rotation_offset)) % (2 * math.pi)
    
    arm1_rotation = arm1_rotation_moving_average.add(arm1_raw_rotation)
    arm2_rotation = arm2_rotation_moving_average.add(arm2_raw_rotation)
    arm3_rotation = turntable_rotation_moving_average.add(arm3_raw_rotation)
    
    #print("r1 " + str(arm1_rotation))
    #print("r2 " + str(arm2_rotation))
    #print("r3 " + str(arm3_rotation))

    x, y, z = determine_pos(arm1_length, arm2_length, offset, arm1_rotation, arm2_rotation, arm3_rotation)

    accumulation_x += (x - previous_x) * sensitivity
    accumulation_y += (y - previous_y) * sensitivity
    accumulation_z += (y - previous_z) * sensitivity

    previous_x = x
    previous_y = y
    previous_z = z
    
    move_x = int(accumulation_x)
    move_y = int(accumulation_y)
    move_z = int(accumulation_z)
    
    # TODO: implement threshold to take into accound total distance
    if abs(accumulation_x) >= threshold or abs(accumulation_y) >= threshold:
        move_x = int(accumulation_x)
        move_y = int(accumulation_y)
        mouse.move(move_x, move_y)
        accumulation_x -= move_x
        accumulation_y -= move_y
    
    # Avoid spamming HID reports, as it slows down the microcontroller immensely 
    if not m1_btn.value:  
        mouse.press(Mouse.LEFT_BUTTON)
    else:
        mouse.release(Mouse.LEFT_BUTTON)
    if not m2_btn.value:  
        mouse.press(Mouse.RIGHT_BUTTON)
    else:
        mouse.release(Mouse.RIGHT_BUTTON)
        
    if not m3_btn.value:  
        mouse.press(Mouse.RIGHT_BUTTON)
    else:
        mouse.release(Mouse.RIGHT_BUTTON)    
        
    #time.sleep(0.005)