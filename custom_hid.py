from moving_average import MovingAverage
import math
import time

class CustomHid:

    def __init__(self, mouse, custom_hid, 
                 arm1_length, arm2_length, base_offset, pen_offset,
                 rotation_sensor_1, rotation_sensor_2, rotation_sensor_3, 
                 button_1, button_2, button_3,
                 sensitivity = 10, mouse_smoothing_count = 3, threshold = 2,
                 profile = 0):
        self.mouse = mouse
        self.custom_hid = custom_hid

        self.arm1_length = arm1_length
        self.arm2_length = arm2_length
        self.base_offset = base_offset
        self.pen_offset = pen_offset

        self.rotation_sensor_1 = rotation_sensor_1
        self.rotation_sensor_2 = rotation_sensor_2
        self.rotation_sensor_3 = rotation_sensor_3
        self.button_1 = button_1
        self.button_2 = button_2
        self.button_3 = button_3

        self.sensitivity = sensitivity
        self.mouse_smoothing_count = mouse_smoothing_count
        self.threshold = threshold
        self.profile = profile

        self.arm1_rotation_moving_average = MovingAverage(size=mouse_smoothing_count)
        self.arm2_rotation_moving_average = MovingAverage(size=mouse_smoothing_count)
        self.turntable_rotation_moving_average = MovingAverage(size=mouse_smoothing_count)

        self.arm1_rotation_offset = 360-286 # Arm 1
        self.arm2_rotation_offset = 360-111 # Arm 2
        self.turntable_rotation_offset = 360-0 # Turntable

        # Previous coordinates
        self.previous_x = 0
        self.previous_y = 0
        self.previous_z = 0

        # Accumulation
        # TODO: Explain this
        self.accumulation_x = 0
        self.accumulation_y = 0
        self.accumulation_z = 0

        # Move
        self.move_x = 0
        self.move_y = 0
        self.move_z = 0

        self.arm1_rotation_offset = 0
        self.arm2_rotation_offset = 0
        self.turntable_rotation_offset = 0

        self.arm1_rotation_offset = math.radians(360-286) # Arm 1
        self.arm2_rotation_offset = math.radians(360-111) # Arm 2
        self.turntable_rotation_offset = math.radians(360-0) # Turntable

    def get_rotations(self):
        arm1_raw_rotation = ((self.rotation_sensor_1.angle / 4096) * 2 * math.pi + self.arm1_rotation_offset) % (2 * math.pi)
        arm2_raw_rotation = ((self.rotation_sensor_2.angle / 4096) * 2 * math.pi + self.arm2_rotation_offset) % (2 * math.pi)
        turntable_raw_rotation = ((self.rotation_sensor_3.angle / 4096) * 2 * math.pi + self.turntable_rotation_offset) % (2 * math.pi)
        
        arm1_rotation = self.arm1_rotation_moving_average.add(arm1_raw_rotation)
        arm2_rotation = self.arm2_rotation_moving_average.add(arm2_raw_rotation)
        turntable_rotation = self.turntable_rotation_moving_average.add(turntable_raw_rotation)

        # print(arm1_rotation, arm2_rotation, turntable_rotation)

        return arm1_rotation, arm2_rotation, turntable_rotation
           
    def determine_pos(self):
        """
        :param l1: Length of arm 1 (mm)
        :param l2: Length of arm 2 (mm)
        :param rotation_1: Rotation of arm 1 (radians)
        :param rotation_2: Rotation of arm 2 (radians)
        :param rotation_3: Turntable rotation (radians)
        :return: A tuple containing the x, y, and z coordinates of the endpoint
        """
        rotation_1, rotation_2, rotation_3 = self.get_rotations()
        # rotation_1 = 1.03
        # rotation_2 = 1.48
        # rotation_3 = 0.86
        # print(int(rotation_1), int(rotation_2), int(rotation_3))
            
        x1 = (math.sin(rotation_1) * self.arm1_length + self.base_offset)
        y1 = 0 #-self.pen_offset
        z1 = math.cos(rotation_1) * self.arm1_length
        # print(x1, y1, z1)
        
        x2 = x1 + math.sin(rotation_2 + rotation_1) * self.arm2_length
        y2 = y1 
        z2 = (z1 + math.cos(rotation_2 + rotation_1) * self.arm2_length)
        # print(x2, y2, z2)
        
        # Apply the turn_table rotation
        x3 = (x2 * math.cos(rotation_3)) - (y2 * math.sin(rotation_3))
        y3 = (x2 * math.sin(rotation_3)) + (y2 * math.cos(rotation_3))
        z3 = z2
        print(rotation_1, rotation_2, rotation_3)
        print(x3, y3, z3)
        # time.sleep(0.05)
        
        return (x3, -z3, y3) # TODO: Why is the frame of reference different?
    
    def callibrate(self):
        arm1_rotation, arm2_rotation, turntable_rotation = self.get_rotations()
        self.arm1_rotation_offset = (2 * math.pi) - arm1_rotation
        self.arm2_rotation_offset = (2 * math.pi) - arm2_rotation
        self.turntable_rotation_offset = (2 * math.pi) - turntable_rotation
        
    def update(self):
        # a, b, c = self.get_rotations()
        # print(determine_height(170, 205, a, b))
        x, y, z = self.determine_pos()
        # print(x, y, z)
        self.accumulation_x += (x - self.previous_x) * self.sensitivity
        self.accumulation_y += (y - self.previous_y) * self.sensitivity
        self.accumulation_z += (z - self.previous_z) * self.sensitivity
        threshold = 0

        self.previous_x = x
        self.previous_y = y
        self.previous_z = z
    
        self.move_x = int(self.accumulation_x)
        self.move_y = int(self.accumulation_y)
        self.move_z = int(self.accumulation_z)
        
        # TODO: implement threshold to take into account total distance
        # if abs(self.accumulation_x) >= threshold or abs(self.accumulation_y) >= threshold:
        self.move_x = int(self.accumulation_x)
        self.move_y = int(self.accumulation_y)
        self.move_z = int(self.accumulation_z)
        
        # z-movement goes unused
        self.accumulation_x -= self.move_x
        self.accumulation_y -= self.move_y
        self.accumulation_z -= self.move_z

        self.mouse.move(self.move_x, self.move_y)
        
        # Avoid spamming HID reports, as it slows down the microcontroller immensely 
        # if not m1_btn.value:  
        #     self.mouse.press(Mouse.LEFT_BUTTON)
        # else:
        #     mouse.release(Mouse.LEFT_BUTTON)
        # if not m2_btn.value:  
        #     mouse.press(Mouse.RIGHT_BUTTON)
        # else:
        #     mouse.release(Mouse.RIGHT_BUTTON)
            
        # if not m3_btn.value:  
        #     mouse.press(Mouse.RIGHT_BUTTON)
        # else:
        #     mouse.release(Mouse.RIGHT_BUTTON)    




def determine_height(l1, l2, rotation_1, rotation_2):
    """
    :param l1: Length of arm 1
    :param l2: Length of arm 2
    :param rotation_1: Rotation of arm 1
    :param rotation_2: Rotation of arm 2
    :return: Z-position of the end point
    """
    rotation_1 = rotation_1
    rotation_2 = rotation_2


    z = (math.cos(rotation_1) * l1) + (math.cos(rotation_1 + rotation_2) * l2)

    return z