#import urllib.request
import json
import gi
gi.require("Aravis", "0.6") # or whatever version number you have installed
from gi.repository import Aravis
import pyyolo
import cv2
import ctypes
import numpy as np
from multiprocessing import pool

with open('./../config.json', 'r') as config_file:
    CONFIG_DATA = json.load(config_file)

STATUS_URL = '192.168.1.112:8000/status'
TRIGGER_FAR_URL = '192.168.1.112:8000/trigger-far'
TRIGGER_CLOSE_URL = '192.168.1.112:8000/trigger-close'
TRIGGER_TRUCK_URL = '192.168.1.112:8000/trigger-truck'

VISION_CAM_1 = ''
VISION_CAM_2 = ''

OVERVIEW_CAM_1 = ''
OVERVIEW_CAM_2 = ''

DETAIL_CAM_1 = ''
DETAIL_CAM_2 = ''
DETAIL_CAM_3 = ''
DETAIL_CAM_4 = ''

VISION_CAM_1_HISTORY = ''
VISION_CAM_2_HISTORY = ''

FAR_TRIGGER_THRESHOLD = 0
CLOSE_TRIGGER_THRESHOLD = 0
TRUCK_TRIGGER_THRESHOLD = 0

darknet_path = './pyyolo/darknet'
datacfg = 'cfg/coco.data'
cfgfile = 'cfg/yolov3-tiny.cfg'
weightfile = '../yolov3-tiny.weights'

thresh = 0.45
hier_thresh = 0.5

def perform_recognition(model, image, threshold):
    boxes = model(image)
    boxRel = boxes.x
    sizeInFrame = 0
    if (boxRel > FAR_TRIGGER_THRESHOLD):
        urllib.request.urlopen(TRIGGER_FAR_URL).read()
    if (boxRel > CLOSE_TRIGGER_THRESHOLD):
        urllib.request.urlopen(TRIGGER_FAR_URL).read()
    if (boxRel > TRUCK_TRIGGER_THRESHOLD):
        urllib.request.urlopen(TRIGGER_FAR_URL).read()

def convert(buf):
        if not buf:
            return None
        pixel_format = buf.get_image_pixel_format()
        bits_per_pixel = pixel_format >> 16 & 0xff
        if bits_per_pixel == 8:
            INTP = ctypes.POINTER(ctypes.c_uint8)
        else:
            INTP = ctypes.POINTER(ctypes.c_uint16)
        addr = buf.get_data()
        ptr = ctypes.cast(addr, INTP)
        im = np.ctypeslib.as_array(ptr, (buf.get_image_height(), buf.get_image_width()))
        im = im.copy()
        return im
    
def GigeStreamer(cam_id):
    camera_id = cam_id
    pyyolo.init(darknet_path, datacfg, cfgfile, weightfile)
    Aravis.enable_interface(camera_id) # using arv-fake-gv-camera-0.6
    camera = Aravis.Camera.new(None)
    stream = camera.create_stream (None, None)
    payload = camera.get_payload ()

    for i in range(0,50):
        stream.push_buffer (Aravis.Buffer.new_allocate (payload))

    print("Starting acquisition")
    camera.start_acquisition()
    while True:
        buffer = stream.try_pop_buffer()
        print(buffer)
        if buffer:
            frame = convert(buffer)
            stream.push_buffer(buffer) #push buffer back into stream
            cv2.imshow("frame", frame)

            # img = cv2.imread(filename)
            img = frame.transpose(2,0,1) # img = img.transpose(2,0,1)
            c, h, w = img.shape[0], img.shape[1], img.shape[2]
            data = img.ravel()/255.0
            data = np.ascontiguousarray(data, dtype=np.float32)
            # perform_recognition()
            outputs = pyyolo.detect(w, h, c, data, thresh, hier_thresh)	
            for output in outputs:
                print(output)

            ch = cv2.waitKey(1) & 0xFF
            if ch == 27 or ch == ord('q'):
                break
            elif ch == ord('s'):
                cv2.imwrite("imagename.png",frame)
    camera.stop_acquisition()
    pyyolo.cleanup()

def main():
    pool = Pool(processes=2)
    visionCamOne = pool.apply_async(GigeStreamer, [VISION_CAM_1])
    #visionCamTwo = pool.apply_async(GigeStreamer, [VISION_CAM_2])

    pool.close()
    pool.join()
