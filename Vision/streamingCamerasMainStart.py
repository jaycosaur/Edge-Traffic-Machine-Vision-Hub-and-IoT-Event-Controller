import gi
import sys
import multiprocessing
import time
import cv2
import urllib.request
import numpy as np 
import ctypes
import uuid
from harvesters.core import Harvester

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

h = Harvester()
h.add_cti_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
h.update_device_info_list()


def worker(camId):


    CAM_NAME = CAM_CONFIG[camId]['name']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']

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
    camIds = ['CAM_1','CAM_2']
    for i in camIds:
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()