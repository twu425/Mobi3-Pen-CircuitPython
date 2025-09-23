import math

class ArmKinematics:
    def __init__(self, arm1_len, arm2_len, base_offset):
        self.arm1_len = arm1_len
        self.arm2_len = arm2_len
        self.base_offset = base_offset

    def calculate_position(self, r1, r2, r3):
        x1 = math.sin(r1) * self.arm1_len
        y1 = self.base_offset
        z1 = math.cos(r1) * self.arm1_len
        x2 = x1 + math.sin(r1 + r2) * self.arm2_len
        z2 = z1 + math.cos(r1 + r2) * self.arm2_len
        x3 = x2 * math.cos(r3) - y1 * math.sin(r3)
        y3 = x2 * math.sin(r3) + y1 * math.cos(r3)
        return x3, y3, z2
