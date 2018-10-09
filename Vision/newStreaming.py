import sys
import multiprocessing
import time
import cv2
import urllib.request
import json
import numpy as np 
from pydarknet import Detector, Image
from harvesters.core import Harvester
from skimage import measure
from imutils import contours
import imutils


thresh = 0.5
hier_thresh = 0.2

datacfg = '/home/server/Projects/YOLO3-4-Py/cfg/coco.data'
cfgfile = '/home/server/Projects/YOLO3-4-Py/cfg/yolov3.cfg'
weightfile = '/home/server/Projects/YOLO3-4-Py/weights/yolov3.weights'

SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'

TRIGGER_FAR_URL = 'http://192.168.1.100:8000/trigger-far'
TRIGGER_CLOSE_URL = 'http://192.168.1.100:8000/trigger-close'
TRIGGER_TRUCK_URL = 'http://192.168.1.100:8000/trigger-truck'
TRIGGER_FAR_FLASH_URL = 'http://192.168.1.100:8000/trigger-far-flash'
TRIGGER_CLOSE_FLASH_URL = 'http://192.168.1.100:8000/trigger-close-flash'
TRIGGER_TRUCK_FLASH_URL = 'http://192.168.1.100:8000/trigger-truck-flash'

CTI_FILE = '/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti'

TIMEOUT_DELAY = 5
triggerDelay = 0.250

LOG = False

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

def sendMessageToSlack(message, color):
    body = {'text': message, "color": color,}  
    req = urllib.request.Request(SLACK_WEBHOOK_URL)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    urllib.request.urlopen(req, jsondataasbytes)

def yoloWorker(camId):
    # declare yolo detector in isolation from camera object for reinitiation of camera under failure.
    print(camId, ' Constructing Yolo Model ...')
    net = Detector(bytes(cfgfile, encoding="utf-8"), bytes(weightfile, encoding="utf-8"), 0,
                   bytes(datacfg, encoding="utf-8"))

    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']

    # main worker event loop, will keep restarting on camera dropout
    while(True):
        print(camId, ' Creating harvester modules and loading genlcam producers ...')
        h = Harvester()
        h.add_cti_file(CTI_FILE)
        h.update_device_info_list()

        try:
            cam = h.create_image_acquisition_manager(serial_number=CAM_NAME)
            print ("Camera found!")
        except:
            print ("Camera Not Found! Waiting 10 seconds and retrying ...")
            time.sleep(10) #sleep for 10 seconds and then retry!
            continue #exit ()

        cam.start_image_acquisition()
        cv2.namedWindow(WINDOW_NAME, flags=0) # create dedicated stream window

        #variable declarations
        lastTime = time.time()
        transposeTime = 0
        i = 0
        numberCars = 0
        lastSnapshot = None
        
        baseColor = (255,255,255)
        baseRes = 400
        scale = 800/1920
        #as percentages to do
        uproadThresh = 240
        truckThresh = 170
        closeThresh = 145
        extraThresh = 50
        leftBound = 50
        leftBound2 = 60
        rightBound = 90
        rightBound2 = 125
        marginOfError = 15
        # rescaling
        factor = baseRes/320
        uproadThresh = int(uproadThresh*factor)
        truckThresh = int(truckThresh*factor)
        closeThresh = int(closeThresh*factor )
        extraThresh = int(50*factor )
        leftBound = int(leftBound*factor )
        leftBound2 = int(leftBound2*factor )
        rightBound = int(125*factor )
        rightBound2 = int(125*factor )

        showLines = False
        showYolo = False

        uproadLastTrigger = time.time()
        truckLastTrigger = time.time()
        closeLastTrigger = time.time()

        IS_CAM_OK = True

        IS_MULTI = False
        
        def fetchBuffer(shared, camera): 
            frame = camera.fetch_buffer()
            shared['buffer'] = frame.payload.components[0].data
            frame.queue()

        while(IS_CAM_OK):
            if IS_MULTI:
                dict = {
                    "buffer": None
                }
                manager = multiprocessing.Manager()
                shared = manager.dict()

                p = multiprocessing.Process(target=fetchBuffer, args=(shared, cam))
                p.start()

                # Wait for 5 seconds or until process finishes
                p.join(TIMEOUT_DELAY)

                print('3')
                # If thread is still active
                if p.is_alive():
                    print('CAM TOOK TOO LONG TO FETCH BUFFER - KILLING AND RESTARTING!')
                    p.terminate()
                    p.join()
                    IS_CAM_OK = False
                    #sendMessageToSlack('Streaming Camera has Failed - Restarting ...', '#ff3300')
            
            frame = cam.fetch_buffer()


            if LOG:
                print(shared['buffer'])

            if(IS_CAM_OK and frame.payload):
                image = frame.payload.components[0].data
                if LOG:
                    print(image)
                small = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
                rgb = cv2.cvtColor(small, cv2.COLOR_BayerRG2RGB)
                img = np.rot90(rgb,1)
                c, h1, w1 = rgb.shape[2], rgb.shape[1], rgb.shape[0]

                img2 = Image(img)
                results = net.detect(img2)

                if LOG:
                    print(results)

                user_input_key = cv2.waitKey(1)

                if user_input_key==113: #q
                    showLines = True
                elif user_input_key==97: #a
                    showLines = False
                elif user_input_key==122: #z
                    showYolo = True
                elif user_input_key==120: #x
                    showYolo = False

                if showLines and camId=='CAM_2':
                        cv2.line(rgb, (uproadThresh,0), (uproadThresh, w1), (255,255,0), 1)
                        cv2.line(rgb, (uproadThresh+marginOfError,0), (uproadThresh+marginOfError, w1), (255,0,0), 1)
                        cv2.line(rgb, (uproadThresh-marginOfError,0), (uproadThresh-marginOfError, w1), (255,0,0), 1)
                        cv2.line(rgb, (truckThresh,0), (truckThresh, w1), (255,255,0), 1)
                        cv2.line(rgb, (truckThresh+marginOfError,0), (truckThresh+marginOfError, w1), (255,0,0), 1)
                        cv2.line(rgb, (truckThresh-marginOfError,0), (truckThresh-marginOfError, w1), (255,0,0), 1)
                        cv2.line(rgb, (closeThresh,0), (closeThresh, w1), (255,255,0), 1)
                        cv2.line(rgb, (closeThresh+marginOfError,0), (closeThresh+marginOfError, w1), (255,0,0), 1)
                        cv2.line(rgb, (closeThresh-marginOfError,0), (closeThresh-marginOfError, w1), (255,0,0), 1)
                        cv2.line(rgb, (0,rightBound), (h1, rightBound), (255,255,255), 1)
                        cv2.line(rgb, (0,leftBound2), (h1, leftBound2), (255,255,255), 1)
                        cv2.line(rgb, (0,leftBound), (h1, leftBound), (255,255,255), 1)

                for cat, score, bounds in results:
                        x, y, w, h = bounds
                        x, y = (h1-int(y), int(x))
                        x1,y1,x2,y2 = [int(x-h/2),int(y-w/2),int(x+h/2),int(y+w/2)]

                        type = str(cat.decode("utf-8"))
                        color = baseColor
                        if showYolo and h>5:
                            cv2.rectangle(rgb, (x1,y1),(x2,y2),color)
                            cv2.circle(rgb, (int(x), int(y)), int(2),(0, 255, 0), 3)

                        currentTime = time.time()
                        if y <= rightBound and camId=='CAM_2' and h>10 and w>10:
                            if x>=uproadThresh-10 and x<=uproadThresh+10 and y>=leftBound2 and (currentTime-uproadLastTrigger)>triggerDelay:
                                urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                                if LOG:
                                    print('FAR TRIG')
                                uproadLastTrigger = currentTime
                            if x>=truckThresh-marginOfError and x<=truckThresh+marginOfError and y>=leftBound and (currentTime-truckLastTrigger)>triggerDelay:
                                urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                                if LOG:
                                    print('TRUCK TRIG')
                                numberCars += 1
                                truckLastTrigger = currentTime
                            if x>=closeThresh-marginOfError*2 and x<=closeThresh+marginOfError*2 and y>=leftBound and (currentTime-closeLastTrigger)>triggerDelay:
                                urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                                if LOG:
                                    print('CLOSE TRIG')
                                closeLastTrigger = currentTime
                        
                        if camId=='CAM_1':
                            if y1<=rightBound2   and y2>=rightBound2 and False :
                                urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                                numberCars += 1

                if IS_ROTATE:
                    cv2.imshow(WINDOW_NAME, np.rot90(rgb))
                else:
                    cv2.imshow(WINDOW_NAME, rgb)
                frame.queue()
                cv2.waitKey(1)
                print("Count: ", numberCars, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime))
                lastTime = time.time()
                i += 1

        #IF CAM NOT OK
        cam.stop_image_acquisition()
        cam.destroy()

def openCvWorker(camId):
    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']

    h = Harvester()
    h.add_cti_file(CTI_FILE)
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
    frame = 0
    numberCars = 0
    lastSnapshot = None
    cv2.namedWindow(WINDOW_NAME, flags=0)

    carColor = (255,0,0)
    busColor = (0,255,0)
    truckColor = (0,0,255)
    phoneColor = (0,255,255)
    baseColor = (255,255,255)

    baseRes = 300
    scale = 800/1920

    #as percentages

    uproadThresh = 220 
    truckThresh = 160
    closeThresh = 100
    extraThresh = 50
    leftBound = 50
    leftBound2 = 60
    rightBound = 80
    rightBound2 = 125
    marginOfError = 10

    
    factor = baseRes/320
    uproadThresh = int(uproadThresh*factor)
    truckThresh = int(truckThresh*factor)
    closeThresh = int(closeThresh*factor )
    extraThresh = int(50*factor )
    leftBound = int(leftBound*factor )
    leftBound2 = int(leftBound2*factor )
    rightBound = int(rightBound*factor )
    rightBound2 = int(125*factor )

    showLines = False
    showYolo = False

    triggerDelay = 0.250
    uproadLastTrigger = time.time()
    truckLastTrigger = time.time()
    closeLastTrigger = time.time()

    while(True):
        buffer = cam.fetch_buffer()
        payload = buffer.payload.components
        if LOG:
            print(payload)
        if(payload):
            image = payload[0].data
            if showLines or showYolo:
                conver = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
                small = cv2.cvtColor(conver, cv2.COLOR_BayerRG2RGB)
                rgb = cv2.cvtColor(conver, cv2.COLOR_BayerRG2GRAY)
            else:
                small = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
                rgb = cv2.cvtColor(small, cv2.COLOR_BayerRG2GRAY)
            
            thresh = cv2.threshold(rgb, 200, 255, cv2.THRESH_BINARY)[1]

            labels = measure.label(thresh, neighbors=8, background=0)
            mask = np.zeros(thresh.shape, dtype="uint8")

            if LOG:
                print(labels)

            # loop over the unique components
            for label in np.unique(labels):
                # if this is the background label, ignore it
                if label == 0:
                    continue
                labelMask = np.zeros(thresh.shape, dtype="uint8")
                labelMask[labels == label] = 255
                mask = cv2.add(mask, labelMask)

            if len(np.unique(labels))>0:
                cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = cnts[0] if imutils.is_cv2() else cnts[1]
                #cnts = contours.sort_contours(cnts)[0]
                
                # loop over the contours
                for (i, c) in enumerate(cnts):
                    currentTime = time.time()
                    # draw the bright spot on the image
                    (x, y, w, h) = cv2.boundingRect(c)
                    ((cX, cY), radius) = cv2.minEnclosingCircle(c)
                    if showYolo:
                        cv2.circle(small, (int(cX), int(cY)), int(5),
                            (0, 0, 255), 3)
                    if cY <= rightBound and cY >= leftBound and camId=='CAM_2':
                        if cX>=uproadThresh-marginOfError and cX<=uproadThresh+marginOfError and (currentTime-uproadLastTrigger)>triggerDelay and cY>=leftBound2:
                            urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                            uproadLastTrigger = currentTime
                            numberCars += 1
                        if cX>=truckThresh-marginOfError and cX<=truckThresh+marginOfError and (currentTime-truckLastTrigger)>triggerDelay:
                            urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                            truckLastTrigger = currentTime
                        if cX>=closeThresh-marginOfError and cX<=closeThresh+marginOfError and (currentTime-closeLastTrigger)>triggerDelay:
                            urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                            closeLastTrigger = currentTime

            # show the output image
            # cv2.imshow("Image", rgb)
            k = cv2.waitKey(1)
            h1, w1 = small.shape[1], small.shape[0]

            if k==113:    # Esc key to stop
                showLines = True
            elif k==97:
                showLines = False
            elif k==122:
                showYolo = True
            elif k==120:
                showYolo = False
                

            if showLines and camId=='CAM_2':
                    cv2.line(small, (uproadThresh,0), (uproadThresh, w1), (255,255,0), 1)
                    cv2.putText(small, 'Up-Road', (uproadThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(small, (truckThresh,0), (truckThresh, w1), (255,255,0), 1)
                    cv2.putText(small, 'Truck', (truckThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(small, (closeThresh,0), (closeThresh, w1), (255,255,0), 1)
                    cv2.putText(small, 'Close', (closeThresh, 50), cv2.FONT_HERSHEY_COMPLEX, 0.2, (255,255,0))

                    cv2.line(small, (0,rightBound), (h1, rightBound), (255,255,255), 1)
                    cv2.line(small, (0,leftBound), (h1, leftBound), (255,255,255), 1)
                    cv2.line(small, (0,leftBound2), (h1, leftBound2), (255,0,255), 1)

            if IS_ROTATE:
                cv2.imshow(WINDOW_NAME, np.rot90(small))
            else:
                cv2.imshow(WINDOW_NAME, small)

            cv2.waitKey(1)
            buffer.queue()
            print("Count: ", numberCars, " Frame: ", frame, " FPS: ", 1.0/(time.time()-lastTime))
            lastTime = time.time()
            frame += 1

    cam.stop_image_acquisition()
    cam.destroy()

# main event
if __name__ == '__main__':
    camIds = ['CAM_2']
    for i in camIds:
        p = multiprocessing.Process(target=openCvWorker, args=(i,))
        p.start()