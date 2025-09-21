from moving_average import MovingAverage
import math
import time
import struct
from adafruit_hid.mouse import Mouse
import json
import microcontroller

class CustomHid:

    SENSITIVITY = 10 
    MOUSE_SMOOTHING = 3 # The last N position captures to average out for a smoother result
    THRESHOLD = 2 # The minimum amount of movement required for movement to be reported
    
    ARM1_LENGTH = 170 # The length of arm 1 (the shorter one) in mm
    ARM2_LENGTH = 205 # The length of arm 2 (the longer one) in mm
    BASE_OFFSET = (45+8+8+21) # The total y distance from the center of the platform to the center of the pen tip when the platform is facing the user

    def __init__(self, 
                 mouse, custom_hid, 
                 rotation_sensor_1, rotation_sensor_2, rotation_sensor_3, 
                 button_1, button_2, button_3,
                 profile = 0):
        
        self.mouse = mouse
        self.custom_hid = custom_hid

        self.rotation_sensor_1 = rotation_sensor_1
        self.rotation_sensor_2 = rotation_sensor_2
        self.rotation_sensor_3 = rotation_sensor_3

        self.button_1 = button_1
        self.button_2 = button_2
        self.button_3 = button_3

        self.profile = profile


        self.last_buttons = 0

        self.arm1_rotation_moving_average = MovingAverage(size=self.MOUSE_SMOOTHING)
        self.arm2_rotation_moving_average = MovingAverage(size=self.MOUSE_SMOOTHING)
        self.turntable_rotation_moving_average = MovingAverage(size=self.MOUSE_SMOOTHING)

        # Previous coordinates
        self.previous_x = 0
        self.previous_y = 0
        self.previous_z = 0

        # Accumulation
        # TODO: Explain this
        self.accumulation_x = 0
        self.accumulation_y = 0
        self.accumulation_z = 0

        self.arm1_rotation_offset = 0
        self.arm2_rotation_offset = 0
        self.turntable_rotation_offset = 0

    def get_rotations(self):
        arm1_raw_rotation = ((self.rotation_sensor_1.angle / 4096) * 2 * math.pi - self.arm1_rotation_offset) % (2 * math.pi)
        arm2_raw_rotation = ((self.rotation_sensor_2.angle / 4096) * 2 * math.pi - self.arm2_rotation_offset) % (2 * math.pi)
        turntable_raw_rotation = ((self.rotation_sensor_3.angle / 4096) * 2 * math.pi - self.turntable_rotation_offset) % (2 * math.pi)
        # print(self.arm1_rotation_offset)

        arm1_rotation = self.arm1_rotation_moving_average.add(arm1_raw_rotation)
        arm2_rotation = self.arm2_rotation_moving_average.add(arm2_raw_rotation)
        turntable_rotation = self.turntable_rotation_moving_average.add(turntable_raw_rotation)
        # print(math.degrees(arm1_rotation), math.degrees(arm2_rotation), math.degrees(turntable_rotation))

        return arm1_rotation, arm2_rotation, turntable_rotation
           
    def determine_pos(self):
        rotation_1, rotation_2, rotation_3 = self.get_rotations()
            
        x1 = math.sin(rotation_1) * self.ARM1_LENGTH
        y1 = self.BASE_OFFSET
        z1 = math.cos(rotation_1) * self.ARM1_LENGTH
        # print(x1, y1, z1)
        
        x2 = x1 + math.sin(rotation_2 + rotation_1) * self.ARM2_LENGTH
        y2 = y1 
        z2 = z1 + math.cos(rotation_2 + rotation_1) * self.ARM2_LENGTH
        # print(x2, y2, z2)
        
        # Apply the turn_table rotation
        x3 = (x2 * math.cos(rotation_3)) - (y2 * math.sin(rotation_3))
        y3 = (x2 * math.sin(rotation_3)) + (y2 * math.cos(rotation_3))
        z3 = z2

        # x3 = x2*math.cos(rotation_3) + z2*math.sin(rotation_3)
        # y3 = y2
        # z3 = -x2*math.sin(rotation_3) + z2*math.cos(rotation_3)
        # print(math.degrees(rotation_1), math.degrees(rotation_2), math.degrees(rotation_3))
        print(rotation_1, rotation_2, rotation_3)
        print(x3, y3, z3)
        # print(self.arm1_rotation_offset, self.arm2_rotation_offset, self.turntable_rotation_offset)
        # time.sleep(0.1)
        
        return (x3, y3, z3) # TODO: Why is the frame of reference different?
    
    def callibrate(self):
        arm1_rotation, arm2_rotation, turntable_rotation = self.get_rotations()
        self.arm1_rotation_offset = arm1_rotation
        self.arm2_rotation_offset = arm2_rotation
        self.turntable_rotation_offset = turntable_rotation  
        self.save_calibrations()
        print("Callibrations saved: ", self.arm1_rotation_offset, self.arm2_rotation_offset, self.turntable_rotation_offset)
        # pass

    # Each offset is stored as a 4-byte float (single precision)
    FORMAT = "fff"  # arm1, arm2, turntable
    def load_calibrations(self):
        size = struct.calcsize(self.FORMAT)
        raw = microcontroller.nvm[:size]
        # If memory looks uninitialized (all 0xFF), set defaults
        if all(b == 0xFF for b in raw):
            self.arm1_rotation_offset = 0.0
            self.arm2_rotation_offset = 0.0
            self.turntable_rotation_offset = 0.0
            print("No callibrations values found.")
        else:
            values = struct.unpack(self.FORMAT, raw)
            self.arm1_rotation_offset, self.arm2_rotation_offset, self.turntable_rotation_offset = values
            print("Callibrated loaded: ", self.arm1_rotation_offset, self.arm2_rotation_offset, self.turntable_rotation_offset)

    
    def save_calibrations(self):
        values = (
            float(self.arm1_rotation_offset),
            float(self.arm2_rotation_offset),
            float(self.turntable_rotation_offset)
        )
        data = struct.pack(self.FORMAT, *values)
        buf = microcontroller.nvm[:]  # copy full NVM contents as a slice
        buf[:len(data)] = data        # overwrite start with our data
        microcontroller.nvm[:] = buf  # write back entire slice
        print("Callibrations saved")

    def update(self):
        # a, b, c = self.get_rotations()
        # print(determine_height(170, 205, a, b))
        x, y, z = self.determine_pos()
        # print(x, y, z)
        self.accumulation_x += (x - self.previous_x) * self.SENSITIVITY
        self.accumulation_y += (y - self.previous_y) * self.SENSITIVITY
        self.accumulation_z += (z - self.previous_z) * self.SENSITIVITY
        threshold = 0

        self.previous_x = x
        self.previous_y = y
        self.previous_z = z

        # TODO: implement threshold to take into account total distance
        # if abs(self.accumulation_x) >= threshold or abs(self.accumulation_y) >= threshold:
        move_x = int(self.accumulation_x)
        move_y = int(self.accumulation_y)
        move_z = int(self.accumulation_z)
        
        self.accumulation_x -= move_x
        self.accumulation_y -= move_y
        self.accumulation_z -= move_z

        # self.profile = 2
        if self.profile == 0:
            self.send_mouse_report(move_x, move_y, z)
        if self.profile == 1:
            self.send_custom_hid_report(self.move_x, self.move_y, self.move_z, 0)


    def send_mouse_report(self, move_x, move_y, z_pos):
        # Only move if non-zero
        print(z_pos)
        if (move_x or move_y) and z_pos < -160:
            self.mouse.move(move_x, move_y)

        if not self.button_1.value:
            print("button") 
        # Build button state bitmask
        buttons = 0
        if not self.button_1.value:
            buttons |= Mouse.LEFT_BUTTON
        if not self.button_2.value:
            buttons |= Mouse.RIGHT_BUTTON
        if not self.button_3.value:
            self.callibrate() #TODO: Probably replace this

        # Only send button state if it changed
        if buttons != self.last_buttons:
            self.mouse.release_all()
            if buttons & Mouse.LEFT_BUTTON:
                self.mouse.press(Mouse.LEFT_BUTTON)
            if buttons & Mouse.RIGHT_BUTTON:
                self.mouse.press(Mouse.RIGHT_BUTTON)
            if buttons & Mouse.MIDDLE_BUTTON:
                self.mouse.press(Mouse.MIDDLE_BUTTON)

            self.last_buttons = buttons

    # Function to send a report using our custom HID device
    def send_custom_hid_report(self, x=0, y=0, z=0, buttons=0):
        def clamp(val):
            return max(-127, min(127, int(val)))
        report = struct.pack('bbbB', clamp(x), clamp(y), clamp(z), buttons & 0xFF)
        # print(f"Report bytes: {report} | x: {clamp(x)}, y: {clamp(y)}, z: {clamp(z)}, buttons: {buttons & 0xFF}")
        self.custom_hid.send_report(report)

