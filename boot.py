import usb_hid

# Custom HID descriptor: Vendor-defined but acts like a 2D mouse
CUSTOM_HID_DESCRIPTOR = bytes((
    0x06, 0x00, 0xFF,   # Usage Page (Vendor Defined 0xFF00)
    0x09, 0x01,         # Usage (0x01)
    0xA1, 0x01,         # Collection (Application)

    # X axis
    0x09, 0x30,         #   Usage (X) -> standard generic desktop usage
    0x15, 0x81,         #   Logical Minimum (-127)
    0x25, 0x7F,         #   Logical Maximum (127)
    0x75, 0x08,         #   Report Size (8 bits)
    0x95, 0x01,         #   Report Count (1)
    0x81, 0x02,         #   Input (Data,Var,Abs)

    # Y axis
    0x09, 0x31,         #   Usage (Y)
    0x15, 0x81,         #   Logical Minimum (-127)
    0x25, 0x7F,         #   Logical Maximum (127)
    0x75, 0x08,         #   Report Size (8 bits)
    0x95, 0x01,         #   Report Count (1)
    0x81, 0x02,         #   Input (Data,Var,Abs)

    # Optional buttons (1 byte, 8 buttons max)
    0x05, 0x09,         #   Usage Page (Buttons)
    0x19, 0x01,         #   Usage Minimum (Button 1)
    0x29, 0x08,         #   Usage Maximum (Button 8)
    0x15, 0x00,         #   Logical Minimum (0)
    0x25, 0x01,         #   Logical Maximum (1)
    0x75, 0x01,         #   Report Size (1 bit)
    0x81, 0x02,         #   Input (Data,Var,Abs)

    0xC0                # End Collection
))

custom_hid = usb_hid.Device(
    report_descriptor=CUSTOM_HID_DESCRIPTOR,
    usage_page=0xFF00,    # Vendor-defined page
    usage=0x01,
    in_report_lengths=(3,),   # X, Y, buttons -> 3 bytes
    out_report_lengths=(0,),  # No output for now
    report_ids=(0,),          # No report ID
)

usb_hid.enable((custom_hid,))
