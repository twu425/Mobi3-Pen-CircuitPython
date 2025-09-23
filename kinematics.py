import math

class ArmKinematics:
    def __init__(self, arm1_len, arm2_len, base_offset):
        self.arm1_len = arm1_len
        self.arm2_len = arm2_len
        self.base_offset = base_offset

    def determine_pos(rotation1, rotation2, rotation3, arm1_length, arm2_length, base_offset):
            
        x1 = math.sin(rotation1) * arm1_length
        y1 = base_offset
        z1 = math.cos(rotation1) * arm1_length
        # print(x1, y1, z1)
        
        x2 = x1 + math.sin(rotation2 + rotation1) * arm2_length
        y2 = y1 
        z2 = z1 + math.cos(rotation2 + rotation1) * arm2_length
        # print(x2, y2, z2)
        
        # Apply the turn_table rotation
        x3 = (x2 * math.cos(rotation3)) - (y2 * math.sin(rotation3))
        y3 = (x2 * math.sin(rotation3)) + (y2 * math.cos(rotation3))
        z3 = z2
        # print(x3, y3, z3)
        # print(self.arm1_rotation_offset, self.arm2_rotation_offset, self.turntable_rotation_offset)
        
        return (x3, y3, z3) 
