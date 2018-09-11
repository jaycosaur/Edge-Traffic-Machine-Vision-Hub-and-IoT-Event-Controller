var TaskRunner = require('terminal-task-runner');
var logger = TaskRunner.logger;
var Shell = TaskRunner.shell
var fs = require('fs');
const moment = require('moment')

const pathToUSB = ""
const pathToProcessed = "./../store/processed/"
const pathToLogs = "./../logs/"

const pathToCache = "/media/transferUSB"
const usbId = 'sdb1' //run lsblk to find out

const asyncreaddir = (path) => {
    return new Promise((resolve, reject) => {
        fs.readdir(path,(err,files)=>{
            if (err) {
                reject(err)
            }
            resolve(files)
        })
    })
}

const createMetaDataFile = async (cb) => {
    logger.info("Creating meta data file")
    const exportTimeUNIX = moment().unix()
    const exportTimeISO = moment().toISOString()
    const countPackages = await asyncreaddir(pathToProcessed).then(res=>res.length)
    const countSightings = await asyncreaddir(pathToProcessed).then(res=>res.length)
    const objToWrite = JSON.stringify({info: {
        exportTimeUNIX,
        "exportTimeISO": exportTimeISO,
        "countPackages": countPackages,
        "countSightings": countSightings,
    }})
    fs.writeFile(`${pathToLogs}meta.json`,objToWrite , 'utf8', (err)=>{
        if(err) throw err
        logger.info("Successfully generated Meta File")
        cb()
    });
    
}

var Task = TaskRunner.Base.extend({
    id: 'exports',
    name: 'Export data to USB Drives',
    position: 2,
    run: function(cons) {
        createMetaDataFile(()=>{
            new Shell([
                `sudo mkdir ${pathToCache}`, //make cache / mount path
                `sudo mount /dev/${usbId} ${pathToCache}`, // mount usb to path
                `rsync -av ${pathToProcessed} ${pathToCache}/packages/`// copy processed files to path
                `rsync -av ${pathToLogs} ${pathToCache}/logs/`// copy logs to path
                `sudo unmount ${pathToCache}`
            ], true).start().then(function() {
                cons();
            }, function(err) {
                cons(err);
            });
        })
    }
});


module.exports = Task;