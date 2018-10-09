// Imports the Google Cloud client library
const { Storage } = require('@google-cloud/storage');
const Firestore = require('@google-cloud/firestore');

const chalk = require('chalk')
const moment = require('moment')
const path = require('path');
const fs = require('fs');
const csv=require('csvtojson')
const CONFIG  =require('./config.json')
const axios = require('axios')

const projectId = "onetask-tfnsw-web"
const bucketName = "onetask-sydney-tfnsw"
// Creates a client

const firestore = new Firestore({
    projectId: projectId,
    keyFilename: '/keys/OneTaskTfNSWWeb-14ae9ec35097.json',
  });

const storage = new Storage({
    projectId: projectId
});

firestore.settings({
    timestampsInSnapshots: true
})



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
    
    const FULL_PATH = PATH_TO_FILES //path.join(process.cwd(), PATH_TO_FILES)
    
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

    if (!hasMetaFile){
        throw new Error('No metafile found at this location. Exiting.')
    }
    
    process.stdout.write(chalk.yellow('Checking path contains image ... '))

    try {
        fs.accessSync(path.join(FULL_PATH))
        log(chalk.green('Store found \u2714'))
    } catch (err) {
        log(chalk.red('Store not found! \u2715'))
    }

    process.stdout.write(chalk.yellow('Checking number of images metadata logs ... '))

    const metaData =  await csv({
        noheader: true,
        headers: ["time","timeUNIX","timeISO","timeGPS","GPS_COORDS","CAM","PLATE","PACKAGE_ID","PATH","ID"]
    }).fromFile(path.join(FULL_PATH,CONFIG.META_FILE_NAME)) 

    let numberOfFilesInMetaData = metaData.length

    // remove duplicates
    const store = {}

    await metaData.forEach(el=>{
        store[el.ID] = el
    })

    // console.log(store)
    await fs.readdirSync(path.join(FULL_PATH)).forEach(file => {
        numberOfFilesInMetaData += 1
    })

    log(chalk.magenta("Number of images in metadata logs: ", numberOfFilesInMetaData))

    // const document = firestore.doc('posts/intro-to-firestore');
    const batch = firestore.batch()

    const storeArray = Object.keys(store).map(key=>store[key])

    /* await storeArray.forEach(el=>{
        let ref = firestore.doc(`records/${el.ID}`)
        batch.set(ref, el)
    }) */

    //const batch = firestore.batch()
    let recordIndex = 0
    let errorqueue = []
    const uploadStartTime = moment()

    const calculateTimeRemainingInMS = (now, start, progress) => {
        return Math.round(now.diff(start)*(1/progress))
    }

    for (const record of storeArray) {
        recordIndex +=1
        let ref = firestore.doc(`records/${record.ID}`)
        const res = await ref.set(record)
        if(res){
            //errorqueue.push(record)
        }
        const timeRemaining = calculateTimeRemainingInMS(moment(),uploadStartTime,recordIndex/numberOfFilesInMetaData)
        console.log(`${recordIndex} out of ${numberOfFilesInMetaData} ( ${Math.round(100*(recordIndex/numberOfFilesInMetaData))}%) | ${errorqueue.length} Error Records | Started: ${uploadStartTime.format('LLLL')} | Est. Time Remaining: ${Math.round(timeRemaining/(1000*60))} minutes| Est. Completed Time: ${uploadStartTime.add(timeRemaining, 'ms').format('LLLL')}`)
    }

    console.log(errorQueue)

    //await batch.commit()

    /* // Enter new data into the document.
    await document.set({
            title: 'Welcome to Firestore',
            body: 'Hello World',
        }).then(() => {
            // Document created successfully.
        }); */

    process.stdout.write(chalk.yellow('Checking number of images in store ... '))
    let numberOfFilesInStore = 0
    await fs.readdirSync(path.join(FULL_PATH)).forEach(file => {
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