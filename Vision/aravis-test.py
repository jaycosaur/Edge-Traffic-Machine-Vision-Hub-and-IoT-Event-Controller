#!/usr/bin/env python

#  If you have installed aravis in a non standard location, you may need
#   to make GI_TYPELIB_PATH point to the correct location. For example:
#
#   export GI_TYPELIB_PATH=$GI_TYPELIB_PATH:/opt/bin/lib/girepositry-1.0/
#
#  You may also have to give the path to libaravis.so, using LD_PRELOAD or
#  LD_LIBRARY_PATH.

import sys
import time

import cv2
import ctypes
import numpy as np
from gi.repository import Aravis

Aravis.enable_interface ("Fake")

try:
    if len(sys.argv) > 1:
        print(sys.argv)
        camera = Aravis.Camera.new(sys.argv[1])
    else:
	    camera = Aravis.Camera.new (None)
except:
    print ("No camera found")
    exit ()

camera.set_region (0,0,128,128)
camera.set_frame_rate (10.0)
camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
stream = camera.create_stream (None, None)

payload = camera.get_payload ()

[x,y,width,height] = camera.get_region ()

print("Camera vendor : %s" %(camera.get_vendor_name ()))
print("Camera model  : %s" %(camera.get_model_name ()))
print("Camera id     : %s" %(camera.get_device_id ()))
print("ROI           : %dx%d at %d,%d" %(width, height, x, y))
print("Payload       : %d" %(payload))
print("Pixel format  : %s" %(camera.get_pixel_format_as_string ()))


for i in range(0,50):
    stream.push_buffer (Aravis.Buffer.new_allocate (payload))

print("Start acquisition")

camera.start_acquisition ()

print("Acquisition")

for i in range(0,2000):
    buffer = stream.pop_buffer()
    print(buffer)
    if buffer:
        stream.push_buffer(buffer)
        pixel_format = buffer.get_image_pixel_format()
        bits_per_pixel = pixel_format >> 16 & 0xff
        if bits_per_pixel == 8:
            INTP = ctypes.POINTER(ctypes.c_uint8)
        else:
            INTP = ctypes.POINTER(ctypes.c_uint16)
        addr = buffer.get_data()
        ptr = ctypes.cast(addr, INTP)
        im = np.ctypeslib.as_array(ptr, (buffer.get_image_height(), buffer.get_image_width()))
        frame = im.copy()
        cv2.imshow("frame", frame)

print("Stop acquisition")

camera.stop_acquisition ()