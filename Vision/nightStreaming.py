import sys
import multiprocessing
import time
import cv2
import urllib.request
import numpy as np 
from pydarknet import Detector, Image
import urllib.request
from harvesters.core import Harvester
from imutils import contours
from skimage import measure

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

    carColor = (255,0,0)
    busColor = (0,255,0)
    truckColor = (0,0,255)
    phoneColor = (0,255,255)
    baseColor = (255,255,255)

    baseRes = 600
    scale = 800/1920

    #as percentages

    uproadThresh = 295
    truckThresh = 220
    closeThresh = 180
    extraThresh = 50
    leftBound = 50
    rightBound = 125
    rightBound2 = 125
    marginOfError = 20

    
    factor = baseRes/320
    uproadThresh = int(uproadThresh*factor)
    truckThresh = int(truckThresh*factor)
    closeThresh = int(closeThresh*factor )
    extraThresh = int(50*factor )
    leftBound = int(50*factor )
    rightBound = int(125*factor )
    rightBound2 = int(125*factor )

    showLines = False
    showYolo = False

    while(True):
        buffer = cam.fetch_buffer()
        payload = buffer.payload.components
        if(payload):
            image = payload[0].data
            small = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
            rgb = cv2.cvtColor(small, cv2.COLOR_BayerRG2RGB)
            thresh = cv2.threshold(rgb, 200, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.erode(thresh, None, iterations=2)
            thresh = cv2.dilate(thresh, None, iterations=4)

            labels = measure.label(thresh, neighbors=8, background=0)
            mask = np.zeros(thresh.shape, dtype="uint8")
            
            # loop over the unique components
            for label in np.unique(labels):
                # if this is the background label, ignore it
                if label == 0:
                    continue
                print(label)
                """ # otherwise, construct the label mask and count the
                # number of pixels 
                labelMask = np.zeros(thresh.shape, dtype="uint8")
                labelMask[labels == label] = 255

                numPixels = cv2.countNonZero(labelMask)
            
                # if the number of pixels in the component is sufficiently
                # large, then add it to our mask of "large blobs"
                if numPixels > 300:
                    mask = cv2.add(mask, labelMask) """

            img = np.rot90(rgb,1)
            c, h1, w1 = rgb.shape[2], rgb.shape[1], rgb.shape[0]

            img2 = Image(img)
            #results = net.detect(img2)
            k = cv2.waitKey(1)

            if k==113:    # Esc key to stop
                showLines = True
            elif k==97:
                showLines = False
            elif k==122:
                showYolo = True
            elif k==120:
                showYolo = False
                

            if showLines and camId=='CAM_2':
                    cv2.line(rgb, (uproadThresh,0), (uproadThresh, w1), (255,255,0), 1)
                    cv2.putText(rgb, 'Up-Road', (uproadThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(rgb, (truckThresh,0), (truckThresh, w1), (255,255,0), 1)
                    cv2.putText(rgb, 'Truck', (truckThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(rgb, (closeThresh,0), (closeThresh, w1), (255,255,0), 1)
                    cv2.putText(rgb, 'Close', (closeThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(rgb, (0,rightBound), (h1, rightBound), (255,255,255), 1)

            if showLines and camId=='CAM_1':
                cv2.line(rgb, (extraThresh,0), (extraThresh, w1), (255,255,0), 1)
                cv2.putText(rgb, 'Up-Road', (extraThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                #cv2.line(rgb, (0,rightBound2), (h1, rightBound2), (255,255,255), 1)

            bounds = 100
            results = []
            for cat, score, bounds in results:
                    x, y, w, h = bounds
                    x, y = (h1-int(y), int(x))
                    x1,y1,x2,y2 = [int(x-h/2),int(y-w/2),int(x+h/2),int(y+w/2)]

                    type = str(cat.decode("utf-8"))
                    color = baseColor
                    if (type == 'car'):
                        color = carColor
                    if (type == 'bus'):
                        color = busColor
                    if (type == 'truck'):
                        color = truckColor
                    if (type == 'phone'):
                        color = phoneColor
                    #x1,y1,x2,y2 = [int(x+w/2),int(y+h/2),int(x-w/2),int(y-h/2)]
                    #cv2.rectangle(rgb, (int(x-w/2),int(y-h/2)),(int(x+w/2),int(y+h/2)),(255,0,0))
                    #cv2.line(rgb, (x1,y1), (x1, y2), color, 2)
                    if showYolo:
                        cv2.rectangle(rgb, (x1,y1),(x2,y2),color)
                        cv2.putText(rgb, str(cat.decode("utf-8")), (int(x), int(y)), cv2.FONT_HERSHEY_COMPLEX, 1, color)

                    #simple trigger
                    if y2 <= rightBound and camId=='CAM_2':
                        if x1>=uproadThresh-marginOfError and x2<=uproadThresh+marginOfError:
                            urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                            numberCars += 1
                        if x1<=truckThresh and x2>=truckThresh:
                            urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                            numberCars += 1
                        if x1<=closeThresh and x2>=closeThresh:
                            urllib.request.urlopen(TRIGGER_CLOSE_URL).read()
                            numberCars += 1
                    
                    if camId=='CAM_1':
                        if y1<=rightBound2   and y2>=rightBound2  :
                            urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                            numberCars += 1
                    

            '''predictions = []
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
                        urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()'''

            if IS_ROTATE:
                cv2.imshow(WINDOW_NAME, np.rot90(mask))
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