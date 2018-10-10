const extractPlateFromImage = require('./utils/extractPlateFromImage')

path = '~/Desktop/ID=e40bcb0b-9fc6-4e58-810c-b98d949d6447_CAM=CAM9_PLATE=ERROR_UNIX=1539120126081.png'

extractPlateFromImage(1, path, ((plate, time, id)=>{
    // move to new path with plate appended to name
    if(plate){
        console.log(plate)
    } else {
        console.log('drrrr')
    }
}))