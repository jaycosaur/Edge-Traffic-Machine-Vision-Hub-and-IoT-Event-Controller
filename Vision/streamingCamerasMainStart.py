import sys
import multiprocessing
import time
import cv2
import urllib.request
import numpy as np 
import pyyolo
import urllib.request
from harvesters.core import Harvester

thresh = 0.5
hier_thresh = 0.2

darknet_path = '/home/server/Projects/pyyolo/darknet'
datacfg = 'cfg/coco.data'
cfgfile = 'cfg/yolov3-tiny.cfg'
weightfile = '../yolov3-tiny.weights'

TRIGGER_FAR_URL = 'http://192.168.1.100:8000/trigger-far'
TRIGGER_CLOSE_URL = 'http://192.168.1.100:8000/trigger-close'
TRIGGER_TRUCK_URL = 'http://192.168.1.100:8000/trigger-truck'
TRIGGER_FAR_FLASH_URL = 'http://192.168.1.100:8000/trigger-far-flash'
TRIGGER_CLOSE_FLASH_URL = 'http://192.168.1.100:8000/trigger-close-flash'
TRIGGER_TRUCK_FLASH_URL = 'http://192.168.1.100:8000/trigger-truck-flash'

CAM_CONFIG = {
    'CAM_1': {
        'name': 'QG0170070015',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070015',
        'rotate': False
    },
    'CAM_2': {
        'name': 'QG0170070016',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070016',
        'rotate': True
    },
}

def worker(camId):
    pyyolo.init(darknet_path, datacfg, cfgfile, weightfile)
    CAM_NAME = CAM_CONFIG[camId]['name']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']
    h = Harvester()
    h.add_cti_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
    h.update_device_info_list()
    try:
        cam = h.create_image_acquisition_manager(serial_number=CAM_NAME)
        print ("Camera found")

    except:
        print ("Camera Not Found")
        exit ()

    cam.start_image_acquisition()

    lastTime = time.time()
    transposeTime = 0
    i = 0
    numberCars = 0
    lastSnapshot = None
    cv2.namedWindow(CAM_NAME, flags=0)

    while(True):
        buffer = cam.fetch_buffer()
        image = buffer.payload.components[0].data
        im = np.zeros((3,image.shape[0],image.shape[1]))
        im[1,:,:] = image.copy()
        c, h, w = im.shape[0], im.shape[1], im.shape[2]
        data = im.ravel()/255.0
        data = np.ascontiguousarray(data, dtype=np.float32)
        predictions = pyyolo.detect(w, h, c, data, thresh, hier_thresh)
        print(predictions)
        
        if IS_ROTATE:
            cv2.imshow(CAM_NAME, np.rot90(image.copy()))
        else:
            cv2.imshow(CAM_NAME, image.copy())

        cv2.waitKey(1)
        buffer.queue()
        
        print("Count: ", numberCars, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime))
        lastTime = time.time()
        i += 1

    cam.stop_image_acquisition()
    cam.destroy()

if __name__ == '__main__':
   # camIds = ['CAM_1','CAM_2']
    camIds = ['CAM_2']
    for i in camIds:
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()