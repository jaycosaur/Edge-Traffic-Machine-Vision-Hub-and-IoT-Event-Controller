const watch = require('node-watch');
const chokidar = require('chokidar')
const logWriter = require('./utils/logEventHandler')
const eventQueue = require('./actions/index')
const config = require('./../config.json')
const chalk = require('chalk');

const RAW_PATH = config.RAW_STORE_PATH
const STAGED_PATH = config.STAGED_STORE_PATH
const PROCESSED_PATH = config.PROCESSED_STORE_PATH

const writeLogger = new logWriter({path: config.EVENT_LOGS_PATH})

//const rawStoreWatcher = watch(RAW_PATH, { recursive: true })
const stagedStoreWatcher = watch(STAGED_PATH, { recursive: true })
//const processedStoreWatcher = watch(PROCESSED_PATH, { recursive: true })

const rawStoreWatcher = chokidar.watch(RAW_PATH, {awaitWriteFinish: true})
const processedStoreWatcher = chokidar.watch(PROCESSED_PATH, {awaitWriteFinish: true})

console.log(chalk.bgGreen.bold.black("STARTING POST PROCESSING SCRIPTS ..."))
console.log(chalk.bgGreen.black(`Now watching '${RAW_PATH}', '${STAGED_PATH}' and '${PROCESSED_PATH}'`))

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

rawStoreWatcher.on('add', function(name) {
            eventQueue({type: "RAW_STORE_FILE_UPDATED", payload: {path: name}})
            writeLogger.write(`${"RAW_STORE_FILE_UPDATED"} | ${name}`)
    })

processedStoreWatcher.on('add', function(name) {
        eventQueue({type: "PROCESSED_STORE_FILE_UPDATED", payload: {path: name}})
        writeLogger.write(`${"PROCESSED_STORE_FILE_UPDATED"} | ${name}`)
})

stagedStoreWatcher.on('change', function(evt, name) {
    switch(evt){
        case "update":
            eventQueue({type: "STAGED_STORE_FILE_UPDATED", payload: {path: name}}) 
            break
        case "remove":
            eventQueue({type: "STAGED_STORE_FILE_REMOVED"}) 
            break
        default:
            null
    }
    writeLogger.write(`${evt} | ${name}`)
});

/* processedStoreWatcher.on('change', function(evt, name) {
    switch(evt){
        case "update":
            eventQueue({type: "PROCESSED_STORE_FILE_UPDATED", payload: {path: name}}) 
            break
        case "remove":
            eventQueue({type: "PROCESSED_STORE_FILE_REMOVED"}) 
            break
        default:
            null
    }
    writeLogger.write(`${evt} | ${name}`)
}); */