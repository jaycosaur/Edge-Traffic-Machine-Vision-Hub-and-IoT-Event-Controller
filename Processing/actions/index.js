const config = require('./../../config.json')
const actionTypes = require('./actionTypes')
const fs = require('fs');
const chalk = require('chalk');
const moment = require('moment')
const imagemin = require('imagemin');
const imageminJpegtran = require('imagemin-jpegtran');
const logWriter = require('./../utils/sightingEventHandler')

const processedRecordLog = new logWriter({path: config.PROCESSED_LOGS_PATH})
//const extractPlateFromImage = require('../utils/extractPlateFromImage')

let rawImageCount = 0

function move(oldPath, newPath, callback) {
    fs.rename(oldPath, newPath, function (err) {
        if (err) {
            if (err.code === 'EXDEV') {
                copy()
            } else {
                callback(err);
            }
            return
        }
        callback()
    });

    function copy() {
        var readStream = fs.createReadStream(oldPath)
        var writeStream = fs.createWriteStream(newPath)
        readStream.on('error', callback)
        writeStream.on('error', callback)
        readStream.on('close', function () {
            fs.unlink(oldPath, callback)
        })
        readStream.pipe(writeStream)
    }
}

const convertNameToObj = (meta) => {
    const fileType = `.${meta.split('.')[1]}`
    const parts = meta.split('.')[0].split("_")
    return parts.reduce((obj,i)=>{
        let attr = i.split("=")
        return {
            ...obj,
            [attr[0]]:attr[1]
        }
    }, {fileType, fileName: meta})
}

const convertObjToName = (attrs) => {
    const fileType = `.${meta.split('.')[1]}`
    const parts = meta.split('.')[0].split("_")
    return parts.reduce((obj,i)=>{
        let attr = i.split("=")
        return {
            ...obj,
            [attr[0]]:attr[1]
        }
    }, {fileType})
}

module.exports = actionHandler = (action) => {
    console.log(chalk.black.bgYellow('Action Received: ', action.type))
    if(action.type === actionTypes.rawStoreFileUpdated){
        const imageInt = rawImageCount + 1
        rawImageCount += 1
        // name will be CAM_XXXX_ISO_XXXX
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType } = convertNameToObj(pathComps[pathComps.length-1])
        // run through alpr
        /* extractPlateFromImage(imageInt, `${config.RAW_STORE_PATH}${action.payload.path.split("/")[1]}`,((plate, time, id)=>{
            // move to new path with plate appended to name
            if(plate){
                move(action.payload.path,`${config.STAGED_STORE_PATH}${timeIso}_CAM_${cameraName}_${plate}_${imageInt}`)
            } else {
                move(action.payload.path,`${config.STAGED_STORE_PATH}${timeIso}_CAM_${cameraName}_ERROR_${imageInt}`)
            }
        })) */
    }
    if(action.type === actionTypes.stagedStoreFileUpdated){
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, PLATE } = convertNameToObj(pathComps[pathComps.length-1])
        // add exif data (waiting on gps)
        const exifDataToWrite = null

        imagemin([action.payload.path], `${config.PROCESSED_STORE_PATH}`, {
            plugins: [imageminJpegtran()]
        }).then(async res => {
            const { data, path } = res[0]
            // delete old file
            await fs.unlink(action.payload.path, (err) => {
                if (err) throw err;
                return 'OK'
            })
        })
    }
    if(action.type === actionTypes.processedStoreFileUpdated){
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, PLATE, fileName } = convertNameToObj(pathComps[pathComps.length-1])
        // add exif data (waiting on gps)
            // get gps
            // strip out details and transform to exif tags
            // write exif tags
        //below goes in exif write callback
        const objToWrite = {
            timeUNIX: UNIX,
            timeISO: moment.unix(UNIX).toISOString(),
            timeGPS: null,
            GPS_COORDS: null,
            CAM,
            PLATE,
            PACKAGE_ID: 0,
            PATH: fileName
        }
        // append new record to main index collection log csv
        processedRecordLog.write(objToWrite)
    }
}