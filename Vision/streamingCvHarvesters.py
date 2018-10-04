import cv2
import numpy as np 
from harvesters.core import Harvester

h = Harvester()
#h.add_cti_file('/usr/local/lib/baumer/libbgapi2_gige.cti')
h.add_cti_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')

h.update_device_info_list()

cv2.namedWindow('Livestream', flags=0)

cam = h.create_image_acquisition_manager(serial_number='QG0170070016')
cam.start_image_acquisition()


lastTime = time.time()
transposeTime = 0
i = 0
numberCars = 0
lastSnapshot = None

while(i<1000):
    print(i)
    cam.fetch_buffer()
    image = buffer.payload.components[0].data
    cv2.imshow("Livestream", image.copy())	
    cv2.waitKey(1)
    print("Count: ", numberCars, " Frame: ", i, " FPS: ", 1.0/(time.time()-lastTime), "RES: ", w," x ", h)
    lastTime = time.time()
    i += 1

cam.stop_image_acquisition()
cam.destroy()