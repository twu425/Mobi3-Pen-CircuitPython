import usb_hid
import supervisor
import usb.core

# usb_hid.disable()

CUSTOM_HID_DESCRIPTOR = bytes((
    0x06, 0x00, 0xFF,   #   Usage Page (Vendor Defined 0xFF00)
    0x09, 0x01,         #   Usage (0x01)
    0xA1, 0x01,         #   Collection (Application)
    0x85, 0x04,         #   Report ID (4)
    
    # X axis
    0x09, 0x30,         #   Usage (X)
    0x15, 0x81,         #   Logical Minimum (-127)
    0x25, 0x7F,         #   Logical Maximum (127)
    0x75, 0x08,         #   Report Size (8)
    0x95, 0x01,         #   Report Count (1)
    0x81, 0x02,         #   Input (Data,Var,Abs)

    # Y axis
    0x09, 0x31,         #   Usage (Y)
    0x15, 0x81,         #   Logical Minimum (-127)
    0x25, 0x7F,         #   Logical Maximum (127)
    0x75, 0x08,
    0x95, 0x01,
    0x81, 0x02,         #   Input (Data,Var,Abs)

    # Scroll wheel (Z axis)
    0x09, 0x38,         #   Usage (Wheel)
    0x15, 0x81,         #   Logical Minimum (-127)
    0x25, 0x7F,         #   Logical Maximum (127)
    0x75, 0x08,
    0x95, 0x01,
    0x81, 0x02,         #   Input (Data,Var,Rel) - REL if you want "scroll steps"

    # Optional buttons (1 byte, up to 8 buttons)
    0x05, 0x09,         #   Usage Page (Buttons)
    0x19, 0x01,         #   Usage Minimum (Button 1)
    0x29, 0x08,         #   Usage Maximum (Button 8)
    0x15, 0x00,         #   Logical Minimum (0)
    0x25, 0x01,         #   Logical Maximum (1)
    0x75, 0x01,         #   Report Size (1)
    0x95, 0x08,         #   Report Count (8 bits -> 1 byte)
    0x81, 0x02,         #   Input (Data,Var,Abs)


    # 3 floats (x_f, y_f, z_f) - each float is 32 bits (4 bytes)
    0x09, 0x40,         # Usage (Vendor-defined float X)
    0x09, 0x41,         # Usage (Vendor-defined float Y)
    0x09, 0x42,         # Usage (Vendor-defined float Z)
    0x15, 0x00,         # Logical Minimum (0) - floats are handled by host
    0x26, 0xFF, 0xFF,   # Logical Maximum (65535) - placeholder for float scaling
    0x75, 0x20,         # Report Size 32 bits
    0x95, 0x03,         # Report Count 3
    0x81, 0x02,         # Input (Data,Var,Abs)

    0xC0                # End Collection
))

custom_hid = usb_hid.Device(
    report_descriptor=CUSTOM_HID_DESCRIPTOR,
    usage_page=0xFF00,    # Vendor-defined page
    usage=0x01,
    in_report_lengths=(16,),   # X, Y, Wheel, Buttons -> 4 bytes
    out_report_lengths=(0,),
    report_ids=(4,), 
)

# supervisor.set_usb_identification(
#     manufacturer="Twu425",
#     product="My Thingy",
#     vid=0x239A,   # Adafruit's vendor ID
#     pid=0x80F4    # A "random" product ID I made
# )

# Note to self: if enabling the other devices, make sure to create its respective HID object in code.py or the reports will fail
usb_hid.enable(
    (#  usb_hid.Device.KEYBOARD,
     usb_hid.Device.MOUSE,
    #  usb_hid.Device.CONSUMER_CONTROL,
     custom_hid,),     
)

# # Gamepad report descriptor from adafruit for reference on how to setup HID devices (https://learn.adafruit.com/custom-hid-devices-in-circuitpython/report-descriptors)
# GAMEPAD_REPORT_DESCRIPTOR = bytes((
#     0x05, 0x01,  # Usage Page (Generic Desktop Ctrls)
#     0x09, 0x05,  # Usage (Game Pad)
#     0xA1, 0x01,  # Collection (Application)
#     0x85, 0x04,  #   Report ID (4)
#     0x05, 0x09,  #   Usage Page (Button)
#     0x19, 0x01,  #   Usage Minimum (Button 1)
#     0x29, 0x10,  #   Usage Maximum (Button 16)
#     0x15, 0x00,  #   Logical Minimum (0)
#     0x25, 0x01,  #   Logical Maximum (1)
#     0x75, 0x01,  #   Report Size (1)
#     0x95, 0x10,  #   Report Count (16)
#     0x81, 0x02,  #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
#     0x05, 0x01,  #   Usage Page (Generic Desktop Ctrls)
#     0x15, 0x81,  #   Logical Minimum (-127)
#     0x25, 0x7F,  #   Logical Maximum (127)
#     0x09, 0x30,  #   Usage (X)
#     0x09, 0x31,  #   Usage (Y)
#     0x09, 0x32,  #   Usage (Z)
#     0x09, 0x35,  #   Usage (Rz)
#     0x75, 0x08,  #   Report Size (8)
#     0x95, 0x04,  #   Report Count (4)
#     0x81, 0x02,  #   Input (Data,Var,Abs,No Wrap,Linear,Preferred State,No Null Position)
#     0xC0,        # End Collection
# ))
# gamepad = usb_hid.Device(
#     report_descriptor=GAMEPAD_REPORT_DESCRIPTOR,
#     usage_page=0x01,           # Generic Desktop Control
#     usage=0x05,                # Gamepad
#     report_ids=(4,),           # Descriptor uses report ID 4.
#     in_report_lengths=(6,),    # This gamepad sends 6 bytes in its report.
#     out_report_lengths=(0,),   # It does not receive any reports.
# )
# usb_hid.enable(
#     (usb_hid.Device.KEYBOARD,
#      usb_hid.Device.MOUSE,
#      usb_hid.Device.CONSUMER_CONTROL,
#      gamepad)
# )
