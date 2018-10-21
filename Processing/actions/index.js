const config = require('./../../config.json')
const actionTypes = require('./actionTypes')
const fs = require('fs');
const chalk = require('chalk');
const moment = require('moment');
const logWriter = require('./../utils/sightingEventHandler')
const axios = require('axios')
const encode = require('./../utils/addChunkToPng')
const processedRecordLog = new logWriter({path: config.PROCESSED_LOGS_PATH})

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

const end_timeout = 1000;

module.exports = actionHandler = (action) => {
    //console.log(chalk.black.bgYellow('Action Received: ', action.type))
    if(action.type === actionTypes.rawStoreFileUpdated){
        const pathComps = action.payload.path.split("/")
        const { CAM, UNIX, fileType, ID, PLATE, fileName } = convertNameToObj(pathComps[pathComps.length-1])

        function checkEnd(path, prev) {
            fs.stat(path, function (err, stat) {
                // Replace error checking with something appropriate for your app.
                if (err) throw err;
                if (stat.mtime.getTime() === prev.mtime.getTime()) {
                    axios.get('http://192.168.1.100:8000/gps-coords')
                        .then(function (response) {
                            const { lat, lon, time } = response.data
                            const objToWrite = {
                                ID: ID,
                                timeUNIX: UNIX,
                                timeISO: moment.unix(Math.round(UNIX/1000)).toISOString(),
                                timeGPS: time,
                                GPS_COORDS: `${lat}, ${lon}`,
                                CAM,
                                PLATE,
                                PATH: fileName
                            }
                            processedRecordLog.write(objToWrite)
                            return response.data
                        }).then(data => {
                            encode({
                                    direction_of_travel: "west",
                                    gps_latitude: data.lat,
                                    gps_longitude: data.lon,
                                    gps_time_iso: data.time,
                                    capture_time_unixms: UNIX,
                                }, action.payload.path, `${config.PROCESSED_STORE_PATH}ID=${ID}_CAM=${CAM}_PLATE=${'ERROR'}_UNIX=${UNIX}${fileType}`,
                                () => {
                                    // delete file at action.payload.path
                                    fs.unlink(action.payload.path,(err)=>{
                                        if (err) console.log(err);
                                    })
                                }
                            )
                        })
                }
                else
                    setTimeout(checkEnd, end_timeout, path, stat);
            });
        }

        fs.stat(action.payload.path, function (err, stat) {
            // Replace error checking with something appropriate for your app.
            if (err) console.log(err);
            setTimeout(checkEnd, end_timeout, action.payload.path, stat);
        });

        
                
    }
}