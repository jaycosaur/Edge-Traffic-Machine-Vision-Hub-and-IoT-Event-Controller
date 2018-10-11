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
import signal


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
grayThresh = 150

LOG = False

CAM_CONFIG = {
    'CAM_1': {
        'name': 'QG0170070016',
        'window': 'WIDE-TRIGGER',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070016',
        'rotate': True
    },
    'CAM_2': {
        'name': 'QG0170070015',
        'window': 'UPROAD-TRIGGER',
        'pixel_format': 'MONO8',
        'ref': 'QG0170070015',
        'rotate': False
    }
}

THRESHOLDS = {
    'DAY': {
        'uproadThresh': 235,
        'truckThresh': 155,
        'closeThresh': 110,
        'extraThresh': 50,
        'leftBound': 50,
        'leftBound2': 60,
        'rightBound': 90,
        'rightBound2': 125,
        'marginOfError': 15
    },
    'NIGHT': {
        'uproadThresh': 230,
        'truckThresh': 155,
        'closeThresh': 90,
        'extraThresh': 50,
        'leftBound': 50,
        'leftBound2': 60,
        'rightBound': 80,
        'rightBound2': 125,
        'marginOfError': 10   
    }
}

class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

def sendMessageToSlack(message, color):
    body = {'text': message, "color": color,}  
    req = urllib.request.Request(SLACK_WEBHOOK_URL)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(body)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    urllib.request.urlopen(req, jsondataasbytes)

def mainWorker(camId):
    # declare yolo detector in isolation from camera object for reinitiation of camera under failure.
    print(camId, ' Constructing Yolo Model ...')
    net = Detector(bytes(cfgfile, encoding="utf-8"), bytes(weightfile, encoding="utf-8"), 0, bytes(datacfg, encoding="utf-8"))

    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']
    # main worker event loop, will keep restarting on camera dropout

    #variable declarations
    lastTime = time.time()
    transposeTime = 0
    frameCount = 0
    numberCars = 0
    lastSnapshot = None
    baseColor = (255,255,255)
    baseRes = 400
    scale = 800/1920
    factor = baseRes/320
    showLines = False
    showYolo = False
    IS_CAM_OK = True
    MODE = "DAY"
    CLOSE_TRIGGER_METHOD = "DELAY" # DELAY, CALC

    # SET MODE BASED ON TIME
    
    # SET THRESHES LOCALLY
    uproadThresh = 0 
    truckThresh = 0
    closeThresh = 0
    extraThresh = 0
    leftBound = 0
    leftBound2 = 0
    rightBound = 0
    rightBound2 = 0
    marginOfError = 0

    def setThresholds(MODE, factor):
        thresh = THRESHOLDS[MODE]
        nonlocal uproadThresh
        nonlocal truckThresh
        nonlocal closeThresh
        nonlocal extraThresh
        nonlocal leftBound
        nonlocal leftBound2
        nonlocal rightBound
        nonlocal rightBound2
        nonlocal marginOfError
        uproadThresh = int(thresh['uproadThresh']*factor)
        truckThresh = int(thresh['truckThresh']*factor)
        closeThresh = int(thresh['closeThresh']*factor)
        extraThresh = int(thresh['extraThresh']*factor)
        leftBound = int(thresh['leftBound']*factor)
        leftBound2 = int(thresh['leftBound2']*factor)
        rightBound = int(thresh['rightBound']*factor)
        rightBound2 = int(thresh['rightBound2']*factor)
        marginOfError = int(thresh['marginOfError']*factor)

    setThresholds(MODE, factor)
    while(True):
        try:
            print(camId, "Creating harvester modules and loading genlcam producers ...")
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

            uproadLastTrigger = time.time()
            truckLastTrigger = time.time()
            closeLastTrigger = time.time()
            uproadTruckDelay = 0.0

            def setUproadTruckDelay():
                nonlocal uproadTruckDelay
                nonlocal uproadLastTrigger
                nonlocal truckLastTrigger
                if truckLastTrigger > uproadLastTrigger and truckLastTrigger-uproadLastTrigger<5:
                    uproadTruckDelay = truckLastTrigger-uproadLastTrigger
                    
            while(IS_CAM_OK):
                try:
                    with timeout(seconds=3, error_message='FETCH_ERROR'):
                        frame = cam.fetch_buffer()
                except:
                    IS_CAM_OK = False
                    print('CAM TOOK TOO LONG TO FETCH BUFFER - KILLING AND RESTARTING!')
                    sendMessageToSlack('Streaming Camera has Failed - Restarting ...', '#ff3300')
                if(IS_CAM_OK and frame.payload.components):
                    image = frame.payload.components[0].data
                    if LOG:
                        print(image)
                    # USER CONTROLS
                    user_input_key = cv2.waitKey(1)
                    if user_input_key==113: #q
                        showLines = True
                    elif user_input_key==97: #a
                        showLines = False
                    elif user_input_key==122: #z
                        showYolo = True
                    elif user_input_key==120: #x
                        showYolo = False
                    elif user_input_key==119: #w
                        MODE="DAY"
                        setThresholds("DAY", factor)
                        # CHANGE EXPOSURE AND GAIN
                    elif user_input_key==115: #s
                        MODE="NIGHT"
                        setThresholds("NIGHT", factor)
                    elif user_input_key==101: #o
                        CLOSE_TRIGGER_METHOD = "CALC"
                    elif user_input_key==100: #l
                        CLOSE_TRIGGER_METHOD = "DELAY"

                    frameScaled = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
                    frameColorised = cv2.cvtColor(frameScaled, cv2.COLOR_BayerRG2RGB)
                    c, h1, w1 = frameColorised.shape[2], frameColorised.shape[1], frameColorised.shape[0]
                    # SHOW LINES SECTION
                    if showLines and camId=='CAM_1' and MODE=="DAY":
                        cv2.line(frameColorised, (uproadThresh,0), (uproadThresh, w1), (255,255,0), 1)
                        cv2.line(frameColorised, (uproadThresh+marginOfError,0), (uproadThresh+marginOfError, w1), (255,0,0), 1)
                        cv2.line(frameColorised, (uproadThresh-marginOfError,0), (uproadThresh-marginOfError, w1), (255,0,0), 1)
                        cv2.line(frameColorised, (truckThresh,0), (truckThresh, w1), (255,255,0), 1)
                        cv2.line(frameColorised, (truckThresh+marginOfError,0), (truckThresh+marginOfError, w1), (255,0,0), 1)
                        cv2.line(frameColorised, (truckThresh-marginOfError,0), (truckThresh-marginOfError, w1), (255,0,0), 1)
                        cv2.line(frameColorised, (closeThresh,0), (closeThresh, w1), (255,255,0), 1)
                        cv2.line(frameColorised, (closeThresh+marginOfError,0), (closeThresh+marginOfError, w1), (255,0,0), 1)
                        cv2.line(frameColorised, (closeThresh-marginOfError,0), (closeThresh-marginOfError, w1), (255,0,0), 1)
                        cv2.line(frameColorised, (0,rightBound), (h1, rightBound), (255,255,255), 1)
                        cv2.line(frameColorised, (0,leftBound2), (h1, leftBound2), (255,255,255), 1)
                        cv2.line(frameColorised, (0,leftBound), (h1, leftBound), (255,255,255), 1) 

                    if showLines and camId=='CAM_1' and MODE=="NIGHT":
                        cv2.line(frameColorised, (uproadThresh,0), (uproadThresh, w1), (255,255,0), 1)
                        cv2.line(frameColorised, (truckThresh,0), (truckThresh, w1), (255,255,0), 1)
                        cv2.line(frameColorised, (closeThresh,0), (closeThresh, w1), (255,255,0), 1)
                        cv2.line(frameColorised, (0,rightBound), (h1, rightBound), (255,255,255), 1)
                        cv2.line(frameColorised, (0,leftBound), (h1, leftBound), (255,255,255), 1)
                        cv2.line(frameColorised, (0,leftBound2), (h1, leftBound2), (255,0,255), 1)
                    # PROCESSING SPECIFIC
                    if MODE=="NIGHT":
                        frameGray = cv2.cvtColor(frameScaled, cv2.COLOR_BayerRG2GRAY)
                        thresh = cv2.threshold(frameGray,  grayThresh, 255, cv2.THRESH_BINARY)[1]
                        labels = measure.label(thresh, neighbors=8, background=0)
                        mask = np.zeros(thresh.shape, dtype="uint8")
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
                            # loop over the contours
                            for (i, c) in enumerate(cnts):
                                currentTime = time.time()
                                # draw the bright spot on the image
                                (x, y, w, h) = cv2.boundingRect(c)
                                ((cX, cY), radius) = cv2.minEnclosingCircle(c)
                                if showYolo:
                                    cv2.circle(frameColorised, (int(cX), int(cY)), int(5),
                                        (0, 0, 255), 3)
                                if cY <= rightBound and cY >= leftBound and camId=='CAM_1':
                                    if cX>=uproadThresh-marginOfError and cX<=uproadThresh+marginOfError and (currentTime-uproadLastTrigger)>triggerDelay and cY>=leftBound2:
                                        urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                                        uproadLastTrigger = currentTime
                                        numberCars += 1
                                    if cX>=truckThresh-marginOfError and cX<=truckThresh+marginOfError and (currentTime-truckLastTrigger)>triggerDelay:
                                        urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                                        truckLastTrigger = currentTime
                                        setUproadTruckDelay()
                                    if cX>=closeThresh-marginOfError and cX<=closeThresh+marginOfError and (currentTime-closeLastTrigger)>triggerDelay:
                                        urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                                        closeLastTrigger = currentTime
                    if MODE=="DAY":
                        img = np.rot90(frameColorised, 1)
                        img2 = Image(img)
                        results = net.detect(img2)
                        for cat, score, bounds in results:
                                x, y, w, h = bounds
                                x, y = (h1-int(y), int(x))
                                x1,y1,x2,y2 = [int(x-h/2),int(y-w/2),int(x+h/2),int(y+w/2)]

                                type = str(cat.decode("utf-8"))
                                color = baseColor
                                if showYolo and h>5:
                                    cv2.rectangle(frameColorised, (x1,y1),(x2,y2),color)
                                    cv2.circle(frameColorised, (int(x), int(y)), int(2),(0, 255, 0), 3)

                                currentTime = time.time()
                                if y <= rightBound and camId=='CAM_1' and h>10 and w>10:
                                    if x>=uproadThresh-10 and x<=uproadThresh+10 and y>=leftBound2 and (currentTime-uproadLastTrigger)>triggerDelay:
                                        urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                                        numberCars += 1
                                        uproadLastTrigger = currentTime
                                    if x>=truckThresh-marginOfError and x<=truckThresh+marginOfError and y>=leftBound and (currentTime-truckLastTrigger)>triggerDelay:
                                        urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                                        truckLastTrigger = currentTime
                                        setUproadTruckDelay()
                                    if x>=closeThresh-marginOfError*2 and x<=closeThresh+marginOfError*2 and y>=leftBound and (currentTime-closeLastTrigger)>triggerDelay:
                                        urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                                        closeLastTrigger = currentTime

                    # DISPLAY FRAME IN WINDOW
                    if IS_ROTATE:
                        cv2.imshow(WINDOW_NAME, np.rot90(frameColorised))
                    else:
                        cv2.imshow(WINDOW_NAME, frameColorised)
                            
                    frame.queue()
                    cv2.waitKey(1)
                    if frameCount%10==0:
                        print("mode:", MODE,"close mode:", CLOSE_TRIGGER_METHOD, "cars:", numberCars, "frame:", frameCount, "fps:", int(1.0/(time.time()-lastTime)),"trigger dif",uproadTruckDelay)
                    lastTime = time.time()
                    frameCount += 1

            #IF CAM NOT OK
            cam.stop_image_acquisition()
            cam.destroy()
        except Exception as e:
            print ("Critical Script error! Trying again in 5 seconds ...")
            print(e)
            time.sleep(5) #sleep for 10 seconds and then retry!

# main event
if __name__ == '__main__':
    camIds = ['CAM_1']
    for i in camIds:
        p = multiprocessing.Process(target=mainWorker, args=(i,))
        p.start()