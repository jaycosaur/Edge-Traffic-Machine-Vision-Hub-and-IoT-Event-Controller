import gi
import sys
import time
import cv2
#import aravis
import numpy as np 
from PIL import Image
import ctypes

gi.require_version('Aravis', '0.4')

from gi.repository import Aravis


#ids = Aravis.get_device_ids()
#print(ids)

#print(dir(Aravis))

Aravis.enable_interface ("Fake")

try:
    cam = Aravis.Camera.new('Daheng Imavision-QV0180080308')
    print ("Camera found")
except:
    print ("No camera found")
    exit ()


cam.set_region (0,0,2448,2048)
cam.set_frame_rate (20.0)
#cam.set_exposure_time(500000)
cam.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)

payload = cam.get_payload()

[x,y,width,height] = cam.get_region ()

print ("Camera vendor : %s" %(cam.get_vendor_name ()))
print ("Camera model  : %s" %(cam.get_model_name ()))
print ("Camera id     : %s" %(cam.get_device_id ()))
print ("ROI           : %dx%d at %d,%d" %(width, height, x, y))
print ("Payload       : %d" %(payload))
print ("Pixel format  : %s" %(cam.get_pixel_format_as_string ()))

pixels = [' ','.',',',',','`',':',';','i','+','t','l','O','I','X','#','#']
pixels = pixels[::-1] #flip at github's black on white

stream = cam.create_stream (None, None)

cv2.namedWindow('capture', flags=0)


cam.start_acquisition()

for i in range(0,1000):
    stream.push_buffer(Aravis.Buffer.new_allocate(payload))
    buffer = stream.pop_buffer ()
    b = ctypes.cast(buffer.data,ctypes.POINTER(ctypes.c_uint8))
    im = np.ctypeslib.as_array(b, (height, width))
    #im = im.copy()
    #print("shape: ", im.shape)
    print("Frame: ", i, " Time: ", time.time())
    cv2.imshow("capture", im.copy())
    cv2.waitKey(1)
    #cv2.waitKey(0)
    #print("------------------------");
    '''for col in range(0,1530*2048,48*2048):
            c = b[col:(col+2048):24]
            print("".join([pixels[int(ci/16)] for ci in c]))'''

cam.stop_acquisition ()

""" [x,y,width,height] = cam.get_region()


imageBuffer = stream.pop_buffer()

print(imageBuffer)

#dataFromBuffer2 = imageBuffer.get_data()
dataFromBuffer = ctypes.cast(imageBuffer.data,ctypes.POINTER(ctypes.c_ubyte))
ImageIpl = Image.frombytes('L',(width, height),dataFromBuffer)
ImageIpl.save("image_bw.jpeg")
cam.stop_acquisition () """