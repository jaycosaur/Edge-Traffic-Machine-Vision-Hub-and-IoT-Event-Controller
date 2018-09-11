import lightnet

model = lightnet.load(name="yolov2-tiny-voc",path="./yolo/")
image = lightnet.Image.from_bytes(open('./car.png', 'rb').read())

boxes = model(image)