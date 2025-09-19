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
from adafruit_as5600 import AS5600

print("Hello World!")

# Setup HID devices
custom = usb_hid.devices[-1] # The custom HID device is the last in the list from usb_hid.enable() in boot.py
mouse = Mouse(usb_hid.devices)



# Setup 3 I2C busses to handle the three as5600 sensors. They must be on seperate busses as they all use the same slave address.
# i2c1 corresponds to rotation_sensor_3 (the turntable one) and not arm1's rotation sensor. Sorry!
i2c1 = busio.I2C(scl=board.GP1, sda=board.GP0, frequency=100000)
i2c2 = busio.I2C(scl=board.GP7, sda=board.GP6, frequency=100000) 
i2c3 = bitbangio.I2C(scl=board.GP9, sda=board.GP8, frequency=100000) # The pi pico only has 2 hardware i2c busses, so a third one is bit-banged onto GPIO 8 and 9

rotation1_sensor = AS5600(i2c2) # Arm 1 rotation sensor
rotation2_sensor = AS5600(i2c3) # Arm 2 rotation sensor
rotation3_sensor = AS5600(i2c1) # Turntable rotation sensor

print("I am working")

# All measures are in millimeters
arm1_length = 170
arm2_length = 205
base_offset = 45
pen_offset = 12

sensitivity = 10
mouse_smoothing_count = 3 # Determines how many of the last N mouse coordinates to average out for smoother movement
threshold = 2.0  # Ignore movements less than this

# Offsets
arm1_rotation_offset = 360+323 # Arm 1
arm2_rotation_offset = 360+189 # Arm 2
turntable_rotation_offset = 360-11 # Turntable

##############
## Buttons
##############

button1_pin = board.GP11
button2_pin = board.GP12
button3_pin = board.GP13

def registerButton(button_pin):
    button = digitalio.DigitalInOut(button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    return button

button1 = registerButton(button1_pin)
button2 = registerButton(button2_pin)
button3 = registerButton(button3_pin)

##########
## Loop
##########
from custom_hid import CustomHid
device = CustomHid(mouse, custom, 
                   arm1_length, arm2_length, base_offset, pen_offset,
                   rotation1_sensor, rotation2_sensor, rotation3_sensor,
                   button1, button2, button3)
while True:
    device.callibrate()
    device.update()
    time.sleep(0.05)
