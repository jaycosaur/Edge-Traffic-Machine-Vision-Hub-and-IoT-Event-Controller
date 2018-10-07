import gi
import sys
import multiprocessing
import time
import datetime
import cv2
import urllib.request
import numpy as np 
import ctypes
import uuid

gi.require_version('Aravis', '0.4')
from gi.repository import Aravis

Aravis.enable_interface("Fake")

CACHE_PATH = "/home/server/store/raw/"

CAM_CONFIG = {
    'CAM_1': {
        'name': 'Daheng Imaging-CAA18080045',
        'window': 'UPROAD-COLOR',
        'pixel_format': 'BAYERRG8',
        'ref': 'CAM1'
    },
    'CAM_2': {
        'name': 'Daheng Imaging-CAA18080046',
        'window': 'TRUCK-COLOR',
        'pixel_format': 'BAYERRG8',
        'ref': 'CAM2'
    },
    'CAM_3': {
        'name': 'Daheng Imaging-CAA18080047',
        'window': 'CLOSE-COLOR',
        'pixel_format': 'BAYERRG8',
        'ref': 'CAM3'
    },
    'CAM_4': {
        'name': 'Daheng Imaging-CAB18080019',
        'window': 'UPROAD-4K',
        'pixel_format': 'MONO8',
        'ref': 'CAM4'
    },
    'CAM_5': {
        'name': 'Daheng Imaging-CAB18080020',
        'window': 'TRUCK-4K',
        'pixel_format': 'MONO8',
        'ref': 'CAM5'
    },
    'CAM_6': {
        'name': 'Daheng Imaging-CAB18080021',
        'window': 'CLOSE-4K',
        'pixel_format': 'MONO8',
        'ref': 'CAM6'
    },
    'CAM_7': {
        'name': 'Daheng Imavision-QV0170030004',
        'window': 'TRUCK-2K',
        'pixel_format': 'MONO8',
        'ref': 'CAM7'
    },
    'CAM_8': {
        'name': 'Daheng Imavision-QV0180080308',
        'window': 'CLOSE-2K',
        'pixel_format': 'MONO8',
        'ref': 'CAM8'
    },
    'CAM_9': {
        'name': 'Daheng Imavision-QV0180080309',
        'window': 'UPROAD-2K',
        'pixel_format': 'MONO8',
        'ref': 'CAM9'
    }
}

def worker(camId):
    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
    PIXEL_CONFIG = Aravis.PIXEL_FORMAT_MONO_8

    if (CAM_CONFIG[camId]['pixel_format']=="BAYERRG8"):
        PIXEL_CONFIG = Aravis.PIXEL_FORMAT_BAYER_RG_8

    try:
        cam = Aravis.Camera.new(CAM_NAME)
        print ("Camera found")

    except:
        print ("Camera Not Found")
        exit ()

    cam.set_pixel_format (PIXEL_CONFIG)
    cam.get_device().set_string_feature_value("TriggerSource", "Line3")
    cam.get_device().set_string_feature_value("GainAuto", "Off")
    cam.set_acquisition_mode(Aravis.AcquisitionMode.CONTINUOUS)
    cam.set_trigger('On')

    stream = cam.create_stream (None, None)
    cam.get_device().set_string_feature_value("TriggerActivation", 'FallingEdge')
    cam.set_exposure_time(1000)
    #cam.set_gain_auto(Aravis.Auto(2)) #auto gain

    payload = cam.get_payload()

    [x,y,width,height] = cam.get_region ()
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
    print ("Pixel Formats  : %s" %(cam.get_available_pixel_formats_as_display_names()))
    cv2.namedWindow(WINDOW_NAME, flags=0)

    for i in range(0,5):
        stream.push_buffer (Aravis.Buffer.new_allocate (payload))

    cam.start_acquisition()

    lastTime = time.time()



    lastSnapshot = None
    while(True):
        now = datetime.datetime.now()
        #print(now.hour, now.minute)
        #night-mode
        if False:
            cam.set_exposure_time(10000)
            cam.get_device().set_string_feature_value("Gain", 10.0)
        #day-mode
        if False:
            cam.set_exposure_time(500)
            cam.get_device().set_string_feature_value("Gain", 0.0)

        stream.push_buffer(Aravis.Buffer.new_allocate(payload))

        #buffer = stream.try_pop_buffer ()
        buffer = stream.pop_buffer ()
        if(buffer):
            # alt c type definition for bayer-rg-8
            b = ctypes.cast(buffer.data,ctypes.POINTER(ctypes.c_uint8))
            im = np.ctypeslib.as_array(b, (height, width))
            rgb = cv2.cvtColor(im, cv2.COLOR_BayerRG2RGB)
            img = rgb.copy() 
            cv2.putText(img, cam.get_device().get_string_feature_value("GainAuto"), (100, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

            cv2.imshow(WINDOW_NAME, img)	#remove .copy() before production
            #gen uid for image
            uid = uuid.uuid4()

            #name will be ID_XXXX_CAM_XXXX_UNIX_XXXX
            imageName = "ID="+str(uid)+"_CAM="+CAM_CONFIG[camId]['ref']+"_UNIX="+str(round(time.time()*1000))+".png"
            cv2.imwrite(CACHE_PATH+imageName,im.copy())
            print('Camera ', WINDOW_NAME, ' was triggered at ', time.time())
            lastTime = time.time()
            #stream.push_buffer(buffer)
        cv2.waitKey(1)

    cam.stop_acquisition ()

if __name__ == '__main__':
    camIds = ['CAM_1','CAM_2','CAM_3', 'CAM_4', 'CAM_5','CAM_6', 'CAM_7','CAM_8','CAM_9']
    for i in camIds:
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()