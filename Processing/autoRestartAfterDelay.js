const watch = require('node-watch');
const chokidar = require('chokidar')
const logWriter = require('./utils/logEventHandler')
const eventQueue = require('./actions/index')
const config = require('./../config.json')
const chalk = require('chalk');
const axios = require('axios')
const moment = require('moment')
const exec = require('child_process').exec;
const d = require('moment')

const RAW_PATH = config.RAW_STORE_PATH
const BACKUP_PATH = config.BACKUP_LOCATIONS[0]

const rawStoreWatcher = chokidar.watch(RAW_PATH, {awaitWriteFinish: true})
const backupWatcher = chokidar.watch(RAW_PATH, {awaitWriteFinish: true})

let RESET_TIMER_DELAY = 60 //seconds!

if (process.env.DELAY_TIME){
    RESET_TIMER_DELAY = process.env.DELAY_TIME
}

console.log(chalk.bgGreen.bold.black(`RUNNING WATCH SCRIPTS AT A DELAY OF ${RESET_TIMER_DELAY}...`))
console.log(chalk.bgGreen.black(`Now watching '${RAW_PATH}' and '${BACKUP_PATH }'`))

const backupLimitExceeded = () => axios.post(config.SLACK_WEBHOOK_URL, {
    text: "Nothing has been backed up for a while. I'd check those backupz son!",
    color: "#66ff66"
  })

const cameraFailAlert = () => axios.post(config.SLACK_WEBHOOK_URL, {
    text: "Streaming Cameras Have Failed! Reseting. Stay tuned for success message.",
    color: "#66ff66"
})

const cameraBackAlert = () => axios.post(config.SLACK_WEBHOOK_URL, {
    text: "Cameras are back bojack.",
    color: "#66ff66"
})

const cameraReturnedToNormal= () => axios.post(config.SLACK_WEBHOOK_URL, {
    text: "All cameras have resumed normal operations.",
    color: "#66ff66"
})

/* rawStoreWatcher.on('change', function(evt, name) {
    switch(evt){
        case "update":
            eventQueue({type: "RAW_STORE_FILE_UPDATED", payload: {path: name}}) 
            break
        case "remove":
            eventQueue({type: "RAW_STORE_FILE_REMOVED"}) 
            break
        default:
            null
    }
    writeLogger.write(`${evt} | ${name}`)
}) */

let lastRawFile = moment().toISOString()
let lasBackupFile = moment().toISOString()
let hasRawFailed = false
let hasRawRecovered = false

rawStoreWatcher.on('add', (name) => {
    lastRawFile = moment().toISOString()
    if (hasRawFailed){
        hasRawRecovered = true
    }
    hasRawFailed = false
})

backupWatcher.on('add', function(name) {
    lastBackupFile = moment().toISOString()
})

let timeDifferenceRaw = RESET_TIMER_DELAY

function pause(time) {
    return new Promise(resolve => setTimeout(() => {
      resolve();
    }, time)); 
  }

main = async () => {
    while(true){
        //pkill -9 python
        if (!hasRawFailed && moment(lastRawFile).add(timeDifferenceRaw, 's').isBefore(moment())){
            hasRawFailed = true
            exec('pm2 restart streaming-camera',
                (error, stdout, stderr) => {
                    cameraFailAlert()
                })
        }
        if (hasRawRecovered) {
            cameraBackAlert()
            hasRawRecovered = false
        }
        if (false){
            cameraReturnedToNormal()
        }
        if (false){
            backupLimitExceeded()
        }
        await pause(1000)
    }
}

main()