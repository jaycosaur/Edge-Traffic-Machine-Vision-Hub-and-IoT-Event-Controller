const fs = require('fs');
const cv = require('opencv4nodejs');

const sampleVideoPath = "video.mp4"

const cap = new cv.VideoCapture(sampleVideoPath);
 
let frame;
let index = 0;
do {
  frame = cap.read().cvtColor(cv.COLOR_BGR2RGB);
  console.log('frame', index++); 
  console.log(frame)
} while(!frame.empty);