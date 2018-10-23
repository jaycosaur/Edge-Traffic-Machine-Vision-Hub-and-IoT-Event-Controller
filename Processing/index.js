const chokidar = require('chokidar')
const logWriter = require('./utils/logEventHandler')
const eventQueue = require('./actions/index')
const config = require('./../config.json')
const chalk = require('chalk');

const RAW_PATH = config.RAW_STORE_PATH
const writeLogger = new logWriter({path: config.EVENT_LOGS_PATH})

const rawStoreWatcher = chokidar.watch(RAW_PATH, {awaitWriteFinish: true, ignoreInitial: true})

console.log(chalk.bgGreen.bold.black("STARTING POST PROCESSING SCRIPTS ..."))
console.log(chalk.bgGreen.black(`Now watching '${RAW_PATH}'.`))

rawStoreWatcher.on('add', (name) => {
    eventQueue({type: "RAW_STORE_FILE_UPDATED", payload: {path: name}})
    writeLogger.write(`${"RAW_STORE_FILE_UPDATED"} | ${name}`)
})