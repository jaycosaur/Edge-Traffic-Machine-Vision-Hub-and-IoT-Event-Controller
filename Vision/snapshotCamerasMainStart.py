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

    def changeCamStringValue(feature, value):
        cam.get_device().set_string_feature_value(feature, value)
        return cam.get_device().get_string_feature_value(feature)
    
    def changeCamFloatValue(feature, value):
        cam.get_device().set_float_feature_value(feature, value)
        return cam.get_device().get_float_feature_value(feature)

    def changeCamIntegerValue(feature, value):
        cam.get_device().set_integer_feature_value(feature, value)
        return cam.get_device().get_integer_feature_value(feature)

    lastSnapshot = None

    GAIN_AUTO = cam.get_device().get_string_feature_value("GainAuto")
    EXPOSURE_AUTO = cam.get_device().get_string_feature_value("ExposureAuto")
    GAIN = cam.get_device().get_float_feature_value("Gain")
    EXPOSURE = cam.get_device().get_float_feature_value("ExposureTime")

    EXPOSURE_AUTO_MIN = cam.get_device().get_float_feature_value("AutoExposureTimeMin")
    EXPOSURE_AUTO_MAX = cam.get_device().get_float_feature_value("AutoExposureTimeMax")
    GAIN_AUTO_MIN = cam.get_device().get_float_feature_value("AutoGainMin")
    GAIN_AUTO_MAX = cam.get_device().get_float_feature_value("AutoGainMax")

    TRIGGER_DELAY = cam.get_device().get_float_feature_value("TriggerDelay")
    EXPECTED_GRAY = cam.get_device().get_integer_feature_value("ExpectedGrayValue")

    SHOW_VALUES = False
    

    UNIT = 10
    UNIT_MULTI = 1

    #print(dir(cam.get_device()))

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

        k = cv2.waitKey(1)
        #print(k)
        if k==113: #q
            SHOW_VALUES=True
        if k==97: #a
            SHOW_VALUES=False
        if k==49: #1
            GAIN_AUTO=changeCamStringValue('GainAuto', 'Continuous')
            GAIN = cam.get_device().get_float_feature_value("Gain")
        if k==50: #2
            GAIN_AUTO=changeCamStringValue('GainAuto', 'Off')
            GAIN = cam.get_device().get_float_feature_value("Gain")
        if k==51: #3
            EXPOSURE_AUTO=changeCamStringValue('ExposureAuto', 'Continuous')
            EXPOSURE = cam.get_device().get_float_feature_value("ExposureTime")
        if k==32: #4
            EXPOSURE_AUTO=changeCamStringValue('ExposureAuto', 'Off')
            EXPOSURE = cam.get_device().get_float_feature_value("ExposureTime")
        if k==111: #o
            EXPOSURE_AUTO_MIN=changeCamFloatValue('AutoExposureTimeMin', EXPOSURE_AUTO_MIN+UNIT)
        if k==108: #l
            EXPOSURE_AUTO_MIN=changeCamFloatValue('AutoExposureTimeMin', EXPOSURE_AUTO_MIN-UNIT)
        if k==105: #i
            EXPOSURE_AUTO_MAX=changeCamFloatValue('AutoExposureTimeMax', EXPOSURE_AUTO_MAX+UNIT)
        if k==107: #k
            EXPOSURE_AUTO_MAX=changeCamFloatValue('AutoExposureTimeMax', EXPOSURE_AUTO_MAX-UNIT)
        if k==121: #y
            GAIN_AUTO_MIN=changeCamFloatValue('AutoGainMin', GAIN_AUTO_MIN+UNIT)
        if k==104: #h
            GAIN_AUTO_MIN=changeCamFloatValue('AutoGainMin', GAIN_AUTO_MIN-UNIT)
        if k==117: #u
            GAIN_AUTO_MAX=changeCamFloatValue('AutoGainMax', GAIN_AUTO_MAX+UNIT)
        if k==106: #j
            GAIN_AUTO_MAX=changeCamFloatValue('AutoGainMax', GAIN_AUTO_MAX-UNIT)
        if k==116: #t
            TRIGGER_DELAY=changeCamFloatValue('TriggerDelay', TRIGGER_DELAY+UNIT)
        if k==103: #g
            TRIGGER_DELAY=changeCamFloatValue('TriggerDelay', TRIGGER_DELAY-UNIT)
        if k==114: #r
            EXPECTED_GRAY=changeCamFloatValue('ExpectedGrayValue', EXPECTED_GRAY+UNIT)
        if k==102: #f
            EXPECTED_GRAY=changeCamFloatValue('ExpectedGrayValue', EXPECTED_GRAY-UNIT)

        if k==118: #v
            GAIN=changeCamFloatValue('Gain', GAIN+UNIT)
        if k==98: #b
            GAIN=changeCamFloatValue('Gain', GAIN-UNIT)
        if k==110: #n
            EXPOSURE=changeCamFloatValue('ExposureTime', EXPOSURE+UNIT)
        if k==109: #m
            EXPOSURE=changeCamFloatValue('ExposureTime', EXPOSURE-UNIT)

        if k==119: #w
            UNIT = UNIT + 10**UNIT_MULTI
        if k==115: #s
            UNIT = UNIT - 10**UNIT_MULTI
        if k==120: #x
            UNIT = 10
        if k==119: #e
            UNIT_MULTI = UNIT_MULTI + 1
        if k==115: #d
            UNIT_MULTI = UNIT_MULTI - 1
        if k==99: #c
            UNIT_MULTI = 1

        if(buffer):
            # alt c type definition for bayer-rg-8
            b = ctypes.cast(buffer.data,ctypes.POINTER(ctypes.c_uint8))
            im = np.ctypeslib.as_array(b, (height, width))
            rgb = cv2.cvtColor(im, cv2.COLOR_BayerRG2RGB)
            img = rgb.copy()

            """ if k==113:    # Esc key to stop
                showLines = True
            elif k==97: """
            if SHOW_VALUES:
                cv2.putText(img, "GAIN AUTO: "+str(GAIN_AUTO), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "EXPOSURE AUTO: "+str(EXPOSURE_AUTO), (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "EXPOSURE AUTO MIN: "+str(EXPOSURE_AUTO_MIN), (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "EXPOSURE AUTO MAX:" +str(EXPOSURE_AUTO_MAX), (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "GAIN AUTO MIN: "+str(GAIN_AUTO_MIN), (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "GAIN AUTO MIN: "+str(GAIN_AUTO_MAX), (100, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "TRIGGER DELAY: "+str(TRIGGER_DELAY), (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "EXPECTED GRAY: "+str(EXPECTED_GRAY), (100, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)

                cv2.putText(img, "EXPOSURE: "+str(TRIGGER_DELAY), (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "GAIN: "+str(EXPECTED_GRAY), (100, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)

                cv2.putText(img, "UNIT: "+str(UNIT), (100, 550), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)
                cv2.putText(img, "UNIT MULTIPLIER: "+str(UNIT_MULTI), (100, 600), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255,255,255),2,cv2.LINE_AA)

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