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

SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'

TRIGGER_FAR_URL = 'http://192.168.1.100:8000/trigger-far'
TRIGGER_CLOSE_URL = 'http://192.168.1.100:8000/trigger-close'
TRIGGER_TRUCK_URL = 'http://192.168.1.100:8000/trigger-truck'
TRIGGER_FAR_FLASH_URL = 'http://192.168.1.100:8000/trigger-far-flash'
TRIGGER_CLOSE_FLASH_URL = 'http://192.168.1.100:8000/trigger-close-flash'
TRIGGER_TRUCK_FLASH_URL = 'http://192.168.1.100:8000/trigger-truck-flash'

CTI_FILE = '/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti'

TIMEOUT_DELAY = 5
triggerDelay = 0.5
scaledRes = 416
LOG = False
DELAY_TIME_FROM_INIT_TO_TRIGGER = 20

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
    CAM_NAME = CAM_CONFIG[camId]['name']
    WINDOW_NAME = CAM_CONFIG[camId]['window']
    IS_ROTATE = CAM_CONFIG[camId]['rotate']
    # main worker event loop, will keep restarting on camera dropout

    #variable declarations
    lastTime = time.time()
    transposeTime = 0
    frameCount = 0
    avFrameRate = 0
    numberCars = 0
    numberClose = 0
    numberFar = 0
    numberTruck = 0
    lastSnapshot = None
    baseColor = (255,255,255)
    baseRes = scaledRes
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

    isFarClear = True
    isTruckClear = True
    isCloseClear = True

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
    startTime = time.time()
    IS_CAM_OK = True
    while(IS_CAM_OK):
        print(camId, "Creating harvester modules and loading genlcam producers ...")
        h = Harvester()
        h.add_cti_file(CTI_FILE)
        h.update_device_info_list()
        cam = h.create_image_acquisition_manager(serial_number=CAM_NAME)
        print ("Camera found!")
        cam.start_image_acquisition()
        cv2.namedWindow(WINDOW_NAME, flags=0) # create dedicated stream window

        def nothing(x):
            pass

        def toggleBoxes(x, userdata):
            print(x, userdata)
            print('woo')
            if x==1:
                showLines = True
            else:
                showLines = False

        def switchMode(x):
            if x==1:
                MODE = "DAY"
            else:
                MODE = "NIGHT"

        # cv2.setTrackbarPos(trackbarname, winname, pos)

        # create variable track bars
        showBoxes = '0 : BOXES OFF \n1 : BOXES ON'
        autoExposureSwitch = '0 : Auto Exp OFF \n1 : Auto Exp ON'
        autoGainSwitch = '0 : Auto Gain OFF \n1 : Auto Gain ON'
        modeSwitch = '0 : Night Mode\n1 : Day Mode'

        cv2.createTrackbar(showBoxes,WINDOW_NAME,0,1,nothing)
        cv2.createTrackbar('Trigger Reset Delay ms',WINDOW_NAME,0,1000,nothing)
        cv2.createTrackbar(modeSwitch,WINDOW_NAME,0,1,switchMode)
        cv2.createTrackbar('Far Gray',WINDOW_NAME,0,255,nothing)
        cv2.createTrackbar('Truck Gray',WINDOW_NAME,0,255,nothing)
        cv2.createTrackbar('Close Gray',WINDOW_NAME,0,255,nothing)
        cv2.createTrackbar(autoExposureSwitch,WINDOW_NAME,0,1,nothing)
        cv2.createTrackbar(autoGainSwitch,WINDOW_NAME,0,1,nothing)
        cv2.createTrackbar('Exposure',WINDOW_NAME,20,1000,nothing)
        cv2.createTrackbar('Gain',WINDOW_NAME,0,24,nothing)
        # setThresholds("DAY", factor)
        uproadLastTrigger = time.time()
        truckLastTrigger = time.time()
        closeLastTrigger = time.time()
        farStdAv = 0.0
        closeStdAv = 0.0
        truckStdAv = 0.0
        baseAv = 0.0

        while(IS_CAM_OK): # MAIN WHILE LOOP FOR IMAGE ACQUISITION
            with timeout(seconds=1, error_message='FETCH_ERROR'):
                frame = cam.fetch_buffer()

            if(IS_CAM_OK and frame.payload.components):
                image = frame.payload.components[0].data
                frameScaled = cv2.resize(image, dsize=(baseRes, int(baseRes*scale)), interpolation=cv2.INTER_CUBIC)
                frameColorised = cv2.cvtColor(frameScaled, cv2.COLOR_BayerRG2RGB)
                c, h1, w1 = frameColorised.shape[2], frameColorised.shape[1], frameColorised.shape[0]

                # CHECKING POSITION OF ALL TRACKBARS
                print(cv2.getTrackbarPos(showBoxes,WINDOW_NAME))

                if MODE=="NIGHT":
                    farBoxCenter = [97, 295] 
                    farBoxWidth = 15 
                    farBoxHeight = 10

                    truckBoxCenter = [97, 190]
                    truckBoxWidth = 30 
                    truckBoxHeight = 20 

                    closeBoxCenter = [97, 50] 
                    closeBoxWidth = 35
                    closeBoxHeight = 35

                    sdThreshold = 2#32 #30 #2
                    tsdThreshold = 0.8 #32 #0.8
                    csdThreshold = 0.3 #32 #0.3
  
                else: # DAY DEFAULTS
                    farBoxCenter = [97, 298]
                    farBoxWidth = 5
                    farBoxHeight = 10

                    truckBoxCenter = [97, 170]
                    truckBoxWidth = 5
                    truckBoxHeight = 10

                    closeBoxCenter = [97, 50]
                    closeBoxWidth = 15
                    closeBoxHeight = 15

                    sdThreshold = 30#32 #30 #2
                    tsdThreshold = 30 #32 #0.8
                    csdThreshold = 30 #32 #0.3

                triggerBoxFar = frameScaled[farBoxCenter[0]-farBoxWidth:farBoxCenter[0]+farBoxWidth,farBoxCenter[1]:farBoxCenter[1]+farBoxHeight]   #frameScaled[uproadThresh:uproadThresh+boxHeight,farBoxCenter-farBoxWidth:farBoxCenter+farBoxWidth]    
                triggerBoxTruck = frameScaled[truckBoxCenter[0]-truckBoxWidth:truckBoxCenter[0]+truckBoxWidth,truckBoxCenter[1]:truckBoxCenter[1]+truckBoxHeight]  #frameScaled[truckThresh:truckThresh+boxHeight,truckBoxCenter-truckBoxWidth:truckBoxCenter+truckBoxWidth] 
                triggerBoxClose = frameScaled[closeBoxCenter[0]-closeBoxWidth:closeBoxCenter[0]+closeBoxWidth,closeBoxCenter[1]:closeBoxCenter[1]+closeBoxHeight]   #frameScaled[closeThresh:closeThresh+boxHeight,closeBoxCenter-closeBoxWidth:closeBoxCenter+closeBoxWidth] 

                # ARRAY METRICS FOR TRIGGERING
                triggerBoxFarStd= np.mean(triggerBoxFar)
                triggerBoxTruckStd= np.mean(triggerBoxTruck)
                triggerBoxCloseStd= np.mean(triggerBoxClose)

                numberOfFrames = 200

                farStdAv = farStdAv*(numberOfFrames-1)/numberOfFrames + triggerBoxFarStd/numberOfFrames
                truckStdAv = truckStdAv*(numberOfFrames-1)/numberOfFrames + triggerBoxTruckStd/numberOfFrames
                closeStdAv = closeStdAv*(numberOfFrames-1)/numberOfFrames + triggerBoxCloseStd/numberOfFrames

                farDiff = abs(farStdAv -triggerBoxFarStd)
                truckDiff = abs(truckStdAv-triggerBoxTruckStd)
                closeDiff = abs(closeStdAv-triggerBoxCloseStd)
                currentTime = time.time()

                # WAS GOING TO BE USED TO IDENTIFY CARS, NOW JUST A VISUAL AID FOR WHEN ZONES ARE RESETTING OR NOT
                if isFarClear and farDiff>sdThreshold:
                    isFarClear = False
                elif isFarClear == False and (currentTime-uproadLastTrigger)>triggerDelay: 
                    isFarClear = True
                if isTruckClear and truckDiff>tsdThreshold:
                    isTruckClear = False
                elif isTruckClear == False and (currentTime-truckLastTrigger)>triggerDelay: 
                    isTruckClear = True
                if isCloseClear and closeDiff>csdThreshold:
                    isCloseClear = False
                elif isCloseClear == False  and (currentTime-closeLastTrigger)>triggerDelay:
                    isCloseClear = True

                if currentTime-startTime>DELAY_TIME_FROM_INIT_TO_TRIGGER:
                    if farDiff>sdThreshold and (currentTime-uproadLastTrigger)>triggerDelay:
                        urllib.request.urlopen(TRIGGER_FAR_FLASH_URL).read()
                        numberFar += 1
                        uproadLastTrigger = currentTime
                    if truckDiff>tsdThreshold and (currentTime-truckLastTrigger)>triggerDelay:
                        urllib.request.urlopen(TRIGGER_TRUCK_FLASH_URL).read()
                        numberTruck += 1
                        truckLastTrigger = currentTime
                    if closeDiff>csdThreshold and (currentTime-closeLastTrigger)>triggerDelay:
                        urllib.request.urlopen(TRIGGER_CLOSE_FLASH_URL).read()
                        numberClose += 1
                        closeLastTrigger = currentTime

                # SHOW LINES SECTION
                if showLines:
                    cv2.rectangle(frameColorised, (farBoxCenter[1],farBoxCenter[0]-farBoxWidth),(farBoxCenter[1]+farBoxHeight,farBoxCenter[0]+farBoxWidth),(0,255,0) if isFarClear else (0,0,255))
                    cv2.rectangle(frameColorised, (truckBoxCenter[1],truckBoxCenter[0]-truckBoxWidth),(truckBoxCenter[1]+truckBoxHeight,truckBoxCenter[0]+truckBoxWidth),(0,255,0) if isTruckClear else (0,0,255))
                    cv2.rectangle(frameColorised, (closeBoxCenter[1],closeBoxCenter[0]-closeBoxWidth),(closeBoxCenter[1]+closeBoxHeight,closeBoxCenter[0]+closeBoxWidth),(0,255,0) if isCloseClear else (0,0,255))

                # DISPLAY FRAME IN WINDOW
                cv2.imshow(WINDOW_NAME, np.rot90(frameColorised) if IS_ROTATE else frameColorised)
                        
                frame.queue()
                cv2.waitKey(1)
                avFrameRate=avFrameRate*49/50+int(1.0/(time.time()-lastTime))/50
                if frameCount%1==0:
                    a = 1
                    #print("CF", numberFar, "CT", numberTruck,"CC", numberClose,"avFPS", int(avFrameRate),"FV", int(triggerBoxFarStd),"TV", int(triggerBoxTruckStd), "CV", int(triggerBoxCloseStd))
                lastTime = time.time()
                frameCount += 1

        #IF CAM NOT OK
        cam.stop_image_acquisition()
        cam.destroy()


mainWorker('CAM_1')