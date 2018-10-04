import gi
import sys
import time
import cv2
import urllib.request
import numpy as np 
import ctypes
import multiprocessing
import pyyolo
gi.require_version('Aravis', '0.4')
from gi.repository import Aravis

darknet_path = './darknet'
datacfg = 'cfg/coco.data'
cfgfile = 'cfg/yolov3-tiny.cfg'
weightfile = '../tiny-yolo.weights'

def worker(camId):
    pyyolo.init(darknet_path, datacfg, cfgfile, weightfile)
    Aravis.enable_interface("Fake")
    try:
        cam = Aravis.Camera.new(camId)
        print ("Camera found")
    except:
        print ("No camera found")
        exit ()

    thresh = 0.45
    hier_thresh = 0.5

    #cam.set_region (0,0,2048,1536)
    #cam.set_region (0,0,512,512)
    #cam.set_frame_rate (10.0)
    #cam.set_exposure_time(500000)
    #cam.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)

    #print(dir(cam))


    stream = cam.create_stream (None, None)

    payload = cam.get_payload()

    [x,y,width,height] = cam.get_region ()

    print ("Camera vendor : %s" %(cam.get_vendor_name ()))
    print ("Camera model  : %s" %(cam.get_model_name ()))
    print ("Camera id     : %s" %(cam.get_device_id ()))
    print ("ROI           : %dx%d at %d,%d" %(width, height, x, y))
    print ("Payload       : %d" %(payload))
    print ("Pixel format  : %s" %(cam.get_pixel_format_as_string ()))

    

    #cv2.namedWindow('Live Stream', flags=0)
    cv2.namedWindow(camId, flags=0)

    #rint(dir(stream))

    #for i in range(0,50):
            #stream.push_buffer (Aravis.Buffer.new_allocate (payload))


    cam.start_acquisition()

    lastTime = time.time()
    transposeTime = 0
    i = 0

    while(True):
        stream.push_buffer(Aravis.Buffer.new_allocate(payload))
        buffer = stream.pop_buffer ()
        transposeTime=time.time()
        b = ctypes.cast(buffer.data,ctypes.POINTER(ctypes.c_uint8))
        im = np.ctypeslib.as_array(b, (height, width))
        #im = im.copy()
        #print("shape: ", im.shape)
        #cv2.imshow("Live Stream", im.copy())
        gray = im.copy()
        cv2.imshow(camId, gray)
        #im = np.zeros((3,gray.shape[0],gray.shape[1]))
        #im[1,:,:] = gray
        #im = cv2.cvtColor(gray,cv2.COLOR_GRAY2RGB)
        im = np.stack((im,)*3,-1)
        im = im.transpose(2,0,1)
        c, h, w = im.shape[0], im.shape[1], im.shape[2]
        #print(im.shape)
        #cv2.imshow(camId, im.copy())
        im = im.ravel()/255.0
        #print(im.shape)
        data = np.ascontiguousarray(im, dtype=np.float32)
        #print("TRANS-FPS: ", 1.0/(time.time()-transposeTime))
        predictions = pyyolo.detect(w, h, c, data, thresh, hier_thresh)	
        # { 'left':0, 'right': 767, 'top': 0, 'bottom': x, class': x, prob: x, }
        for output in predictions:
            left, right, top, bottom, what, prob = output['left'],output['right'],output['top'],output['bottom'],output['class'],output['prob']
            print(output)
            if( what == 'car' ):
                d_from_top = top
                d_from_bottom = bottom
                d_from_left = left
                d_from_right = right
                d_height = top
                d_width = left
                if (d_height>0.5):
                    print(output)
                    #trigger other cameras
        cv2.waitKey(1)
        print("CAM: ", camId, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime), "RES: ", h," x ", w)
        lastTime = time.time()
        i += 1
    cam.stop_acquisition ()

if __name__ == '__main__':
    camIds = ['Daheng Imavision-QV0180080308']
    #camIds = ['Daheng Imavision-QV0180080308','Daheng Imavision-QV0170030004']
    for i in camIds:
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()