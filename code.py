# code.py
import usb_hid
import time

custom = usb_hid.devices[0]

# Function to send a report
def send_report(x=0, y=0, buttons=0):
    # x and y must be signed bytes (-127 to 127)
    x_byte = x & 0xFF
    y_byte = y & 0xFF
    buttons_byte = buttons & 0xFF
    report = bytes([x_byte, y_byte, buttons_byte])
    custom.send_report(report)

# Test loop: move mouse diagonally while clicking Button 1
while True:
    send_report(x=10, y=10, buttons=0b00000001)  # move X+10, Y+10, Button 1 pressed
    time.sleep(0.1)
    send_report(x=-10, y=-10, buttons=0)         # move X-10, Y-10, no buttons
    time.sleep(0.1)
# I don't know what I did, but it gave me errors until I nuked the entire flash