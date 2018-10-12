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
const uuidv4 = require('uuid/v4')

const projectId = "onetask-tfnsw-web"
const bucketName = "onetask-sydney-tfnsw"
// Creates a client

const CAM_CONFIG = {
    'CAM1': {
        'name': 'Daheng Imaging-CAA18080045',
        'window': 'UPROAD-COLOR',
        'pixel_format': 'BAYERRG8',
        'ref': 'CAM1',
        'ANGLE': 'UPROAD',
        'TYPE': 'COLOR'
    },
    'CAM2': {
        'name': 'Daheng Imaging-CAA18080046',
        'window': 'TRUCK-COLOR',
        'pixel_format': 'BAYERRG8',
        'ref': 'CAM2',
        'ANGLE': 'TRUCK',
        'TYPE': 'COLOR'
    },
    'CAM3': {
        'name': 'Daheng Imaging-CAA18080047',
        'window': 'CLOSE-COLOR',
        'pixel_format': 'BAYERRG8',
        'ref': 'CAM3',
        'ANGLE': 'CLOSE',
        'TYPE': 'COLOR'
    },
    'CAM4': {
        'name': 'Daheng Imaging-CAB18080019',
        'window': 'UPROAD-4K',
        'pixel_format': 'MONO8',
        'ref': 'CAM4',
        'ANGLE': 'UPROAD',
        'TYPE': '4K'
    },
    'CAM5': {
        'name': 'Daheng Imaging-CAB18080020',
        'window': 'TRUCK-4K',
        'pixel_format': 'MONO8',
        'ref': 'CAM5',
        'ANGLE': 'TRUCK',
        'TYPE': '4K'
    },
    'CAM6': {
        'name': 'Daheng Imaging-CAB18080021',
        'window': 'CLOSE-4K',
        'pixel_format': 'MONO8',
        'ref': 'CAM6',
        'ANGLE': 'CLOSE',
        'TYPE': '4K'
    },
    'CAM7': {
        'name': 'Daheng Imavision-QV0170030004',
        'window': 'TRUCK-2K',
        'pixel_format': 'MONO8',
        'ref': 'CAM7',
        'ANGLE': 'TRUCK',
        'TYPE': '2K'
    },
    'CAM8': {
        'name': 'Daheng Imavision-QV0180080308',
        'window': 'CLOSE-2K',
        'pixel_format': 'MONO8',
        'ref': 'CAM8',
        'ANGLE': 'CLOSE',
        'TYPE': '2K'
    },
    'CAM9': {
        'name': 'Daheng Imavision-QV0180080309',
        'window': 'UPROAD-2K',
        'pixel_format': 'MONO8',
        'ref': 'CAM9',
        'ANGLE': 'UPROAD',
        'TYPE': '2K'
    }
}

const firestore = new Firestore({
    projectId: projectId,
    keyFilename: process.env.gcloudkeypath,
  });

const storage = new Storage({
    projectId: projectId,
    keyFilename: process.env.gcloudkeypath,
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
        headers: ["time","timeUNIX","timeISO","timeGPS","GPS_COORDS","CAM","PLATE","PATH","ID"]
    }).fromFile(path.join(FULL_PATH,CONFIG.META_FILE_NAME)) 

    // remove duplicates
    const store = {}

    await metaData.forEach(el=>{
        store[el.ID] = el
    })

    // const document = firestore.doc('posts/intro-to-firestore');
    // const batch = firestore.batch()

    const storeArray = Object.keys(store).map(key=>store[key])
    let numberOfFilesInMetaData = storeArray.length

    log(chalk.magenta("Number of images in metadata logs: ", numberOfFilesInMetaData))

    /* await storeArray.forEach(el=>{
        let ref = firestore.doc(`records/${el.ID}`)
        batch.set(ref, el)
    }) */

    const calculateTimeRemainingInMS = (now, start, progress) => {
        return Math.round(now.diff(start)*(1/progress))
    }

    process.stdout.write(chalk.yellow('Checking number of images in store ... '))
    let numberOfFilesInStore = 0
    const filesInStore = []

    await fs.readdirSync(path.join(FULL_PATH)).forEach(file => {
        filesInStore.push(file)
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
        log(chalk.bgYellow("Number of images in store does not match number in metadata."))
        //process.exit()
    }

    log(chalk.bgGreen.black('Processing Part 1 ...'))
    const imagesInStore = filesInStore.filter(file=>file.includes('.png'))
    log(chalk.bgGreen.black('Processing Part 2 ...'))
    const imagesInStoreNames = imagesInStore.map(i=>i.split('.')[0])

    // create sightings and check that files are present if not remove and log!
    log(chalk.bgGreen.black('Processing Part 3 ...'))
    let storeWithImages = storeArray.map(record => {
        return {
            ...record,
            hasImage: imagesInStore.includes(record.PATH)
        }
    })
    log(chalk.bgGreen.black('Processing Part 4 - linking images with previous and next ...'))

    const camNames = Object.keys(CAM_CONFIG)

    let close2k = storeWithImages.filter(i=>CAM==="CAM8")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let close4k = storeWithImages.filter(i=>CAM==="CAM6")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let closecolor = storeWithImages.filter(i=>CAM==="CAM3")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let truck2k = storeWithImages.filter(i=>CAM==="CAM7")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let truck4k = storeWithImages.filter(i=>CAM==="CAM5")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let truckcolor = storeWithImages.filter(i=>CAM==="CAM2")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let far2k = storeWithImages.filter(i=>CAM==="CAM9")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let far4k = storeWithImages.filter(i=>CAM==="CAM4")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    let farcolor = storeWithImages.filter(i=>CAM==="CAM1")
                    .sort(a.timeUNIX-b.timeUNIX)
                    .map((record,index,arr)=>{
                        const hasNext = index < arr.length-1
                        const hasPrevious = index > 0
                        return ({
                            ...record,
                            previousRecordId: hasPrevious?arr[index-1].ID:null,
                            nextRecordId: hasNext?arr[index+1].ID:null,
                        })
                    })

    log(chalk.bgGreen.black('Processing Part 5 - linking images with same clusters...'))

    closestElement = (valueToMatch, arr) => {
        let closestIndex = -1
        let smallestDiff = Math.abs(valueToMatch-arr[0])
        arr.forEach((val, ind)=>{
            if (Math.abs(val-valueToMatch)<smallestDiff){
                smallestDiff = Math.abs(val-valueToMatch)<smallestDiff
                closestIndex = ind
            }
        })
        return closestIndex
    }
    
    // close 2k -> close 4k and close color

    close2k.map((val,i)=>{
        let id4k = closestElement(val.timeUNIX, close4k.map(i=>i.timeUNIX))
        let idcol = closestElement(val.timeUNIX, closecolor.map(i=>i.timeUNIX))
        // update 4k and col
        close4k[id4k] = {
            ...close4k[id4k],
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: closecolor[idcol].ID,
                ["4K"]: close4k[id4k].ID,
            }
        }
        closecolor[idcol] = {
            ...closecolor[idcol],
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: closecolor[idcol].ID,
                ["4K"]: close4k[id4k].ID,
            }
        }
        return ({
            ...val,
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: closecolor[idcol].ID,
                ["4K"]: close4k[id4k].ID,
            }
        })
    })

    // truck 2k -> truck 4k and truck color

    truck2k.map((val,i)=>{
        let id4k = closestElement(val.timeUNIX, truck4k.map(i=>i.timeUNIX))
        let idcol = closestElement(val.timeUNIX, truckcolor.map(i=>i.timeUNIX))
        // update 4k and col
        truck4k[id4k] = {
            ...truck4k[id4k],
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: truckcolor[idcol].ID,
                ["4K"]: truck4k[id4k].ID,
            }
        }
        truckcolor[idcol] = {
            ...truckcolor[idcol],
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: truckcolor[idcol].ID,
                ["4K"]: truck4k[id4k].ID,
            }
        }
        return ({
            ...val,
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: truckcolor[idcol].ID,
                ["4K"]: truck4k[id4k].ID,
            }
        })
    })

    // far 2k -> far 4k and far color

    far2k.map((val,i)=>{
        let id4k = closestElement(val.timeUNIX, far4k.map(i=>i.timeUNIX))
        let idcol = closestElement(val.timeUNIX, farcolor.map(i=>i.timeUNIX))
        // update 4k and col
        far4k[id4k] = {
            ...far4k[id4k],
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: farcolor[idcol].ID,
                ["4K"]: far4k[id4k].ID,
            }
        }
        farcolor[idcol] = {
            ...farcolor[idcol],
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: farcolor[idcol].ID,
                ["4K"]: far4k[id4k].ID,
            }
        }
        return ({
            ...val,
            CLUSTER: {
                ["2K"]: val.ID,
                ["COLOR"]: farcolor[idcol].ID,
                ["4K"]: far4k[id4k].ID,
            }
        })
    })

    // remake storeWithImages

    storeWithImages = [
        ...close2k,
        ...close4k,
        ...closecolor,
        ...truck2k,
        ...truck4k,
        ...truckcolor,
        ...far2k,
        ...far4k,
        ...farcolor
    ].sort((a,b)=>a.timeUNIX-b.timeUNIX)

    log(chalk.bgGreen.black('Starting upload process ...'))
    log(chalk.bgGreen.black('Creating batch ...'))
    const batchUuid = uuidv4()

    await firestore.doc(`batches/${batchUuid}`).set({
        batchId: batchUuid,
        numberOfImages: numberOfImages,
        numberOfVehicles: storeWithImages.filter(i=>i.CAM==CAM9).length, // FIX LATER ALLIGATOR
        numberOfRecords: storeWithImages.length,
        uploadStart: moment().toISOString()
    })

    log(chalk.bgGreen.black('Adding Records to Database ...'))
    // Adding records to Firestore DB before commencing image uploads
    let recordIndex = 0
    let errorqueue = []
    let uploadStartTime = moment()

    let batch = firestore.batch()

    for (const record of storeWithImages) {
        recordIndex +=1
        let ref = firestore.doc(`records/${record.ID}`)
        batch.set(ref, {
           ...record,
           uploadBatchId: batchUuid,
           CAM: CAM_CONFIG[record.CAM]['window'],
           ...CAM_CONFIG[record.CAM]
        })
        //const res = await ref.set(record)
        if(recordIndex%500==0){
            let uploadSTime = uploadStartTime.clone()
            await batch.commit()
            const timeRemaining = calculateTimeRemainingInMS(moment(),uploadStartTime,recordIndex/numberOfFilesInMetaData)
            console.log(`${recordIndex} out of ${numberOfFilesInMetaData} ( ${Math.round(100*(recordIndex/numberOfFilesInMetaData))}%) | ${errorqueue.length} Error Records | Started: ${uploadStartTime.format('LLLL')} | Est. Time Remaining: ${Math.round(timeRemaining/(1000*60))} minutes| Est. Completed Time: ${uploadSTime.add(timeRemaining, 'ms').format('LLLL')}`)
            batch = firestore.batch()
        }
    }
    await batch.commit()


    log(chalk.bgGreen.black('Completed Record Additions.'))
    process.exit()
    log(chalk.bgGreen.black('Adding Sightings to Database ...'))
    log(chalk.bgGreen.black('Completed Sighting Additions.'))
    log(chalk.bgGreen.black(`Uploading files to Google Cloud Storage Bucket: ${bucketName}`))

    let currentRecordIndex = 0
    let errorQueue = []
    let uploadStart = moment()
    const numberOfImages = imagesInStore.length

    for (const image of imagesInStore) {
        currentRecordIndex +=1
        const when = uploadStart.clone()
        await storage.bucket(bucketName)
            .upload(path.join(FULL_PATH,image), {
                // Support for HTTP requests made with `Accept-Encoding: gzip`
                gzip: true,
                metadata: {
                // Enable long-lived HTTP caching headers
                // Use only if the contents of the file will never change
                // (If the contents will change, use cacheControl: 'no-cache')
                cacheControl: 'public, max-age=31536000',
                },
            }).catch(err=>{
                console.log(err)
                errorQueue.push({ file: image, err })
            })
        const timeRemaining = calculateTimeRemainingInMS(moment(),when,currentRecordIndex/numberOfImages)
        console.log(`${currentRecordIndex} out of ${numberOfImages} ( ${Math.round(100*(currentRecordIndex/numberOfImages))}%) | ${errorQueue.length} Error Images | Started: ${when.format('LLLL')} | Est. Time Remaining: ${Math.round(timeRemaining/(1000*60))} minutes| Est. Completed Time: ${when.add(timeRemaining, 'ms').format('LLLL')}`)
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