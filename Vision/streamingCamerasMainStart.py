import gi
import sys
import time
import cv2
import urllib.request
import numpy as np 
import ctypes
import pyyolo

gi.require_version('Aravis', '0.4')
from gi.repository import Aravis

darknet_path = '../../../Projects/pyyolo/darknet'
datacfg = 'cfg/coco.data'
cfgfile = 'cfg/yolov3-tiny.cfg'
weightfile = '../yolov3-tiny.weights'

TRIGGER_FAR_URL = 'http://192.168.1.100:8000/trigger-far'
TRIGGER_CLOSE_URL = 'http://192.168.1.100:8000/trigger-close'
TRIGGER_TRUCK_URL = 'http://192.168.1.100:8000/trigger-truck'
TRIGGER_FAR_FLASH_URL = 'http://192.168.1.100:8000/trigger-far-flash'
TRIGGER_CLOSE_FLASH_URL = 'http://192.168.1.100:8000/trigger-close-flash'
TRIGGER_TRUCK_FLASH_URL = 'http://192.168.1.100:8000/trigger-truck-flash'


TRIGGER_CAM_CLOSE = 'Daheng Imavision-QG0170070016'
TRIGGER_CAM_FAR = 'Daheng Imavision-QG0170070015'

CAM_1 = 'Daheng Imaging-CAA18080045' #BAYERRG8
CAM_2 = 'Daheng Imaging-CAA18080046' #BAYERRG8
CAM_3 = 'Daheng Imaging-CAA18080047' #BAYERRG8

CAM_4 = 'Daheng Imaging-CAB18080019' #MONO8
CAM_5 = 'Daheng Imaging-CAB18080020' #MONO8
CAM_6 = 'Daheng Imaging-CAB18080021' #MONO8

CAM_7 = 'Daheng Imavision-QV0170030004' #MONO8
CAM_8 = 'Daheng Imavision-QV0180080308' #MONO8
CAM_9 = 'Daheng Imavision-QV0180080309' #MONO8


Aravis.enable_interface("Fake")

try:
    cam = Aravis.Camera.new(TRIGGER_CAM_CLOSE)
    print ("Camera found")
except:
    print ("Camera Not Found")
    exit ()

thresh = 0.5
hier_thresh = 0.2

#cam.set_region (0,0,2048,1536)
#cam.set_region (0,0,512,512)
#cam.set_frame_rate (10.0)
#cam.set_exposure_time(250)
cam.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)

#pyyolo.init(darknet_path, datacfg, cfgfile, weightfile)

print(dir(cam))
cam.set_trigger_source("Line0")

stream = cam.create_stream (None, None)
cam.set_trigger('On')

cam.get_device().set_string_feature_value("TriggerSource", "Software")
cam.set_acquisition_mode(Aravis.AcquisitionMode.CONTINUOUS)

payload = cam.get_payload()

[x,y,width,height] = cam.get_region ()
print(cam.get_device().get_packet_size())
print(cam.get_device().get_string_feature_value("TriggerMode"))
print(cam.get_device().get_available_enumeration_feature_values_as_strings("TriggerSource"))
print(cam.get_device().get_available_enumeration_feature_values_as_strings("TriggerActivation"))

print ("Camera vendor : %s" %(cam.get_vendor_name ()))
print ("Camera model  : %s" %(cam.get_model_name ()))
print ("Camera id     : %s" %(cam.get_device_id ()))
print ("ROI           : %dx%d at %d,%d" %(width, height, x, y))
print ("Payload       : %d" %(payload))
print ("Pixel format  : %s" %(cam.get_pixel_format_as_string ()))
print ("Trigger Source  : %s" %(cam.get_trigger_source()))
print ("Trigger Activation  : %s" %(cam.get_device().get_string_feature_value("TriggerActivation")))
print ("Acquisition Mode  : %s" %(cam.get_acquisition_mode()))
print ("Pixel Formats  : %s" %(cam.get_available_pixel_formats()))
print(cam.get_sensor_size())

exit()

cv2.namedWindow('Livestream', flags=0)
#cv2.namedWindow('Snapshots', flags=0)

for i in range(0,50): #this may need to be zero to ensure real-time
   stream.push_buffer (Aravis.Buffer.new_allocate (payload))

cam.start_acquisition()

lastTime = time.time()
transposeTime = 0
i = 0
numberCars = 0
lastSnapshot = None

while(i<1000):
    print(i)
    stream.push_buffer(Aravis.Buffer.new_allocate(payload))
    buffer = stream.pop_buffer ()
    transposeTime=time.time()
    # alt c type definition for bayer-rg-8
    #print(dir(ctypes))
    b = ctypes.cast(buffer.data,ctypes.POINTER(ctypes.c_uint8))
    im = np.ctypeslib.as_array(b, (height, width))
    #im = im.copy()
    #print("shape: ", im.shape)
    #cv2.imshow("Live Stream", im.copy())
    gray = im.copy()
    
    
    im = np.zeros((3,gray.shape[0],gray.shape[1]))
    im[1,:,:] = gray
    #im = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)
    #im = np.stack((im,)*3,-1)
    #im = im.transpose(2,0,1)
    c, h, w = im.shape[0], im.shape[1], im.shape[2]
    #print(im.shape)
    #cv2.imshow("Snapshots", im.copy())
    im = im.ravel()/255.0
    #print(im.shape)
    #data = np.ascontiguousarray(im, dtype=np.float32)
    #print("TRANS-FPS: ", 1.0/(time.time()-transposeTime))
    predictions = pyyolo.detect(w, h, c, im, thresh, hier_thresh)
    cv2.imshow("Livestream", gray.copy())	
    for output in predictions:
        left, right, top, bottom, what, prob = output['left'],output['right'],output['top'],output['bottom'],output['class'],output['prob']
        #print(output)
        #lastSnapshot = snapshot.copy()
        #cv2.imshow("Snapshots", lastSnapshot)
        if( what == 'car' ):
            d_from_top = top
            d_from_bottom = bottom
            d_from_left = left
            d_from_right = right
            d_height = top
            d_width = left
            if (d_height>0.5):
                #print(output)
                numberCars += 1
                #trigger other cameras
                urllib.request.urlopen(TRIGGER_FAR_URL).read()
                urllib.request.urlopen(TRIGGER_CLOSE_URL).read()
                urllib.request.urlopen(TRIGGER_TRUCK_URL).read()
    cv2.waitKey(1)
    print("Count: ", numberCars, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime), "RES: ", w," x ", h)
    lastTime = time.time()
    i += 1

cam.stop_acquisition ()