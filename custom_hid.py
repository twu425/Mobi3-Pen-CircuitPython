from moving_average import MovingAverage
import math
import time
import struct
from adafruit_hid.mouse import Mouse
import json
import microcontroller
from kinematics import ArmKinematics

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

        self.move_x = 0
        self.move_y = 0
        self.move_z = 0

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
               
    def callibrate(self):
        arm1_rotation, arm2_rotation, turntable_rotation = self.get_rotations()
        self.arm1_rotation_offset = arm1_rotation
        self.arm2_rotation_offset = arm2_rotation
        self.turntable_rotation_offset = turntable_rotation  
        self.save_calibrations()
        print("Callibrations saved: ", self.arm1_rotation_offset, self.arm2_rotation_offset, self.turntable_rotation_offset)
        # pass

    # Each offset is stored as a 4-byte float
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
        r1, r2, r3 = self.get_rotations()
        x, y, z = ArmKinematics.determine_pos(r1, r2, r3, self.ARM1_LENGTH, self.ARM2_LENGTH, self.BASE_OFFSET)

        self.accumulation_x += (x - self.previous_x) * self.SENSITIVITY
        self.accumulation_y += (y - self.previous_y) * self.SENSITIVITY
        self.accumulation_z += (z - self.previous_z) * self.SENSITIVITY

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

        self.profile = 0
        if self.profile == 0:
            self.send_mouse_report(move_x, move_y, z)
        if self.profile == 1:
            self.send_custom_hid_report(self.move_x, self.move_y, self.move_z, 0, r1, r2, r3)


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

    def send_custom_hid_report(self, dx=0, dy=0, dz=0, buttons=0, fx=0.0, fy=0.0, fz=0.0):
        """
        Pack a 16-byte HID report:
        Byte 0: delta X (-127..127)
        Byte 1: delta Y (-127..127)
        Byte 2: delta Z (-127..127)
        Byte 3: buttons (8 bits)
        Bytes 4-7: float X 
        Bytes 8-11: float Y
        Bytes 12-15: float Z
        """
        
        # Helper to clamp deltas to -127..127
        def clamp(val):
            return max(-127, min(127, int(val)))
        
        report = struct.pack(
            '<bbbBfff',   # Little-endian: 3x int8, 1x uint8, 3x float32
            clamp(dx), clamp(dy), clamp(dz), buttons & 0xFF,
            float(fx), float(fy), float(fz)
        )

        # Send to HID device
        self.custom_hid.send_report(report)

