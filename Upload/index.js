// Imports the Google Cloud client library
const { Storage } = require('@google-cloud/storage');
const chalk = require('chalk')
const moment = require('moment')
const path = require('path');
const fs = require('fs');
const csv=require('csvtojson')
const CONFIG  =require('./config.json')

// Creates a client
const storage = new Storage();

const log = console.log

const PATH_TO_FILES = process.argv[2]

const insertRecordIntoDatabase = (record) => {
    // dummy
    return new Promise((resolve, reject)=>{
        setTimeout(()=>resolve(), 750)
    })
}

const main = async () => {
    if (!PATH_TO_FILES){
        log(chalk.bgRed('No Path Has Been Provided. Exited.'))
        process.exit()
    }
    
    const FULL_PATH = path.join(process.cwd(), PATH_TO_FILES)
    
    log(chalk.green.bold('Welcome to the One Task Uploader'))
    
    log(chalk.green('Your path to sync is: ', FULL_PATH))
    
    process.stdout.write(chalk.yellow('Checking path contains metafile ... '))
    let hasMetaFile = false
    
    await fs.readdirSync(FULL_PATH).forEach(file => {
        if(file===CONFIG.META_FILE_NAME){
            hasMetaFile = true
        }
    })

    log(hasMetaFile?chalk.green('Metafile exists \u2714'):chalk.red('Metafile not found!  \u2715'))
    
    process.stdout.write(chalk.yellow('Checking path contains image store ... '))

    try {
        fs.accessSync(path.join(FULL_PATH,CONFIG.STORE_NAME))
        log(chalk.green('Store found \u2714'))
    } catch (err) {
        log(chalk.red('Store not found! \u2715'))
    }

    process.stdout.write(chalk.yellow('Checking number of images metadata logs ... '))

    const metaData =  csv().fromFile(CONFIG.META_FILE_NAME) 

    const numberOfFilesInMetaData = metaData.length

    await fs.readdirSync(path.join(FULL_PATH,CONFIG.STORE_NAME)).forEach(file => {
        numberOfFilesInMetaData += 1
    })

    log(chalk.magenta("Number of images in metadata logs: ", numberOfFilesInMetaData))

    process.stdout.write(chalk.yellow('Checking number of images in store ... '))
    let numberOfFilesInStore = 0
    await fs.readdirSync(path.join(FULL_PATH,CONFIG.STORE_NAME)).forEach(file => {
        numberOfFilesInStore += 1
    })
    log(chalk.magenta("Number of images in store: ", numberOfFilesInStore))

    if (numberOfFilesInMetaData === 0){
        log(chalk.bgRed('No Images present in MetaData Logs. Exited.'))
        process.exit()
    }

    if (numberOfFilesInStore === 0){
        log(chalk.bgRed('No Images present in Store. Exited.'))
        process.exit()
    }

    if (numberOfFilesInMetaData !== numberOfFilesInStore){
        log(chalk.green("Number of images in store does not match number in metadata. Exited."))
        process.exit()
    }


    //log(chalk.bgYellow.black('Starting upload process ...'))
    
    log(chalk.bgGreen.black('Starting upload process ...'))

    const arrayOfItemsToInsert = [
        {
            meta: {id:12345678},
            file: "123456"
        }
    ]

    let currentRecordIndex = 0

    const errorQueue = []

    const uploadStart = moment()

    const calculateTimeRemainingInMS = (now, start, progress) => {
        return Math.round(now.diff(start)*(1/progress))
    }

    for (const record of arrayOfItemsToInsert) {
        currentRecordIndex +=1
        const res = await insertRecordIntoDatabase(record)
        if(res){
            errorQueue.push(record)
        }
        const timeRemaining = calculateTimeRemainingInMS(moment(),uploadStart,currentRecordIndex/numberOfFilesInMetaData)
        console.log(`${currentRecordIndex} out of ${numberOfFilesInMetaData} ( ${Math.round(100*(currentRecordIndex/numberOfFilesInMetaData))}%) | ${errorQueue.length} Error Records | Started: ${uploadStart.format('LLLL')} | Est. Time Remaining: ${Math.round(timeRemaining/(1000*60))} minutes| Est. Completed Time: ${uploadStart.add(timeRemaining, 'ms').format('LLLL')}`)
    }
}

main()



/**
 * TODO(developer): Uncomment the following lines before running the sample.
 */
// const bucketName = 'Name of a bucket, e.g. my-bucket';
// const filename = 'Local file to upload, e.g. ./local/path/to/file.txt';

// Uploads a local file to the bucket

/* storage
  .bucket(bucketName)
  .upload(filename, {
    // Support for HTTP requests made with `Accept-Encoding: gzip`
    gzip: true,
    metadata: {
      // Enable long-lived HTTP caching headers
      // Use only if the contents of the file will never change
      // (If the contents will change, use cacheControl: 'no-cache')
      cacheControl: 'public, max-age=31536000',
    },
  })
  .then(() => {
    console.log(`${filename} uploaded to ${bucketName}.`);
  })
  .catch(err => {
    console.error('ERROR:', err);
  }); */