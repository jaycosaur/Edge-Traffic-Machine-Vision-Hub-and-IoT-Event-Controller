import sys
import multiprocessing
import time
import cv2
import urllib.request
import numpy as np 
from pydarknet import Detector, Image
import urllib.request
from harvesters.core import Harvester

thresh = 0.5
hier_thresh = 0.2

#darknet_path = '/home/server/Projects/pyyolo/darknet'
datacfg = '/home/server/Projects/YOLO3-4-Py/cfg/coco.data'
cfgfile = '/home/server/Projects/YOLO3-4-Py/cfg/yolov3-tiny.cfg'
weightfile = '/home/server/Projects/YOLO3-4-Py/weights/yolov3-tiny.weights'
#cfgfile = 'tiny-yolo/yolov2-tiny.cfg'
#weightfile = 'tiny-yolo/yolov2-tiny.weights'

TRIGGER_FAR_URL = 'http://192.168.1.100:8000/trigger-far'
TRIGGER_CLOSE_URL = 'http://192.168.1.100:8000/trigger-close'
TRIGGER_TRUCK_URL = 'http://192.168.1.100:8000/trigger-truck'
TRIGGER_FAR_FLASH_URL = 'http://192.168.1.100:8000/trigger-far-flash'
TRIGGER_CLOSE_FLASH_URL = 'http://192.168.1.100:8000/trigger-close-flash'
TRIGGER_TRUCK_FLASH_URL = 'http://192.168.1.100:8000/trigger-truck-flash'

CAM_CONFIG = {
    'CAM_1': {
        'name': 'QG0170070015',
        'window': 'UPROAD-TRIGGER',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070015',
        'rotate': False
    },
    'CAM_2': {
        'name': 'QG0170070016',
        'window': 'WIDE-TRIGGER',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070016',
        'rotate': True
    },
}

def worker(camId):    
    net = Detector(bytes(cfgfile, encoding="utf-8"), bytes(weightfile, encoding="utf-8"), 0,
                   bytes(datacfg, encoding="utf-8"))

    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
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
    cv2.namedWindow(WINDOW_NAME, flags=0)

    while(True):
        buffer = cam.fetch_buffer()
        image = buffer.payload.components[0].data
        small = cv2.resize(image, dsize=(960, 600), interpolation=cv2.INTER_CUBIC)
        #clone = small.copy()

        rgb = cv2.cvtColor(small, cv2.COLOR_BayerRG2RGB)
        img = np.rot90(rgb,1)
        c, h1, w1 = rgb.shape[2], rgb.shape[1], rgb.shape[0]

        #img = rgb.transpose(2,0,1)
        #if IS_ROTATE:
             #img = np.rot90(rgb)
             #rgb = np.rot90(rgb)
        #else:
            #img = rgb
        #print(rgb.shape)
        #c, h, w = img.shape[0], img.shape[1], img.shape[2]
        #c, h, w = img.shape[2], img.shape[1], img.shape[0]
        #data = img.ravel()/255.0
        #data = np.ascontiguousarray(data, dtype=np.float32)
        img2 = Image(img)
        results = net.detect(img2)
        print(results)

        for cat, score, bounds in results:
                x, y, w, h = bounds
                x, y = (h1-int(y), int(x))
                x1,y1,x2,y2 = [int(x-h/2),int(y-w/2),int(x+h/2),int(y+w/2)]
                #x1,y1,x2,y2 = [int(x+w/2),int(y+h/2),int(x-w/2),int(y-h/2)]
                #cv2.rectangle(rgb, (int(x-w/2),int(y-h/2)),(int(x+w/2),int(y+h/2)),(255,0,0))
                cv2.rectangle(rgb, (x1,y1),(x2,y2),(255,0,0))
                cv2.putText(rgb, str(cat.decode("utf-8")), (int(x), int(y)), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0))
                numberCars += 1

        #predictions = pyyolo.detect(w, h, c, data, thresh, hier_thresh)

        #im = np.zeros((3,small.shape[1],small.shape[0]))

        #im[0,:,:] = np.rot90(small)
        #im[1,:,:] = np.rot90(small)
        #im[2,:,:] = np.rot90(small)

        #im = rgb
        #print(rgb.shape)
        predictions = []
        #c, h, w = im.shape[0], im.shape[1], im.shape[2]
        
       # im = im.transpose(2,0,1)

        #c, h, w = im.shape[0], im.shape[1], im.shape[2]

        #c, h, w = 1, image.shape[0], image.shape[1]
        #im = image.copy()
        #data = im.ravel()/255.0
        #print(data.shape)
        #data = np.ascontiguousarray(data, dtype=np.float32)
        #print(data.shape)

        for output in predictions:
            left, right, top, bottom, what, prob = output['left'],output['right'],output['top'],output['bottom'],output['class'],output['prob']
            #print(output)
            #lastSnapshot = snapshot.copy()
            #cv2.imshow("Snapshots", lastSnapshot)
            if( what == 'car' ):
                print(output)
                numberCars += 1
                cv2.rectangle(rgb, (50,50), (100,150), (255, 255, 255), 20)
                if ( camId =="CAM_2" ):
                    urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                    urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                    urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()


        if IS_ROTATE:
            cv2.imshow(WINDOW_NAME, rgb)
        else:
            cv2.imshow(WINDOW_NAME, rgb)

        cv2.waitKey(1)
        buffer.queue()
        
        print("Count: ", numberCars, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime))
        lastTime = time.time()
        i += 1

    cam.stop_image_acquisition()
    cam.destroy()

if __name__ == '__main__':
    camIds = ['CAM_2']
    #camIds = ['CAM_1']
    for i in camIds:
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()