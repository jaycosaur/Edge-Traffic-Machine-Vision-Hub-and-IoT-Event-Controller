const fs = require('fs');
const path = require('path');
const prompt = require('prompt');
const { Storage } = require('@google-cloud/storage');
const Firestore = require('@google-cloud/firestore');
const projectId = "onetask-tfnsw-web"
const bucketName = "onetask-sydney-tfnsw"

const argv = require('minimist')(process.argv.slice(2));
let IMAGE_PATH = null

const firestore = new Firestore({
    projectId: projectId,
    keyFilename: process.env.gcloudkeypath,
})

const storage = new Storage({
    projectId: projectId,
    keyFilename: process.env.gcloudkeypath,
})

firestore.settings({
    timestampsInSnapshots: true
})

const convertFromCornersToYoloFormat = (bottomLeft, topRight) => {
    const objectCenterX = (bottomLeft.x + topRight.x)/2
    const objectCenterY = (bottomLeft.y + topRight.y)/2
    const objectWidthX = Math.abs(bottomLeft.x - topRight.x)
    const objectWidthY = Math.abs(bottomLeft.y - topRight.y)

    return {
        objectCenterX,
        objectCenterY,
        objectWidthX,
        objectWidthY,
    }
}

const doesFileExist = (filename, pathToCheck) => {
    if (fs.existsSync(path.join(pathToCheck, filename))) {
       return true
    }
    return false
}

const removeFile = (path) => {
    fs.unlinkSync(path)
}

prompt.start()

prompt.getSync = (params) => {
    return new Promise((res, rej)=> {
        prompt.get(params, function (err, result) {
            if (err){
                rej(err)
            }
            res(result)
        })
    })
}

const main = async () => {
    if (argv['darknet-location']){
        DARKNET_PATH = argv['darknet-location']
    } else {
        console.error("Invalid. You must provide a valid darknet location when running this script with the --darknet-location=<path> argument.")
        process.exit()
    }

    if (argv['image-relative-path']){
        IMAGE_RELATIVE_PATH = argv['image-relative-path']
        IMAGE_PATH = path.join(DARKNET_PATH,argv['image-relative-path'])
    } else {
        console.error("Invalid. You must provide a valid image path when running this script with the --image-relative-path=<path> argument.")
        process.exit()
    }

    // check folder exists
    const imagePathExists = fs.existsSync(IMAGE_PATH)
    if(!imagePathExists){
        console.error("Invalid Path Given. You must provide a valid image path when running this script with the --image-path=<path> argument. The path provided does not exist.")
        process.exit()
    }

     // clear text files if needed
     if (argv['clear-all-text']){
        // remove all text files to reset
        const updatedfilesInImagePath = await fs.readdirSync(path.join(IMAGE_PATH))
        let textFilesInImagePath = updatedfilesInImagePath.map(i=>i.split(".")).filter(i=>i[1]==="txt")
        console.log(`REMOVING ${textFilesInImagePath.length} TEXT FILES`)
        for (const file of textFilesInImagePath) {
            removeFile(path.join(IMAGE_PATH, file.join(".")))
        }
        textFilesInImagePath = []
    }

    

    // get records from cloud portal
    console.log('Fetching records from database ...')

    let ref = firestore.collection('records').where('isReviewedPositiveSighting', '==', true)

    if (argv['vehicle-type']){
        ref = ref.where('vehicleType', '==', argv['vehicle-type'])
    }

    if (argv['sighting-class']){
        ref = ref.where('sightingClass', '==', argv['sighting-class'])
    }

    const DATABASE_RECORDS = await ref.get()
        .then(querySnapshot => {
            const array = []
            querySnapshot.forEach(doc=>{
                array.push(doc.data())
            })
            return array
        })

    console.log('Checking records against local files ...')

    // has a matching image
    // get files in current directory
    // calculate missing files

    const filesInImagePath = await fs.readdirSync(path.join(IMAGE_PATH))
    const imagesInImagePath = filesInImagePath.map(i=>i.split(".")).filter(i=>i[1]==="png")
    const hasNoImage = DATABASE_RECORDS.filter(i=>imagesInImagePath.map(i=>i[0]).indexOf(i.ID)===-1)

    // check ok to download
    const schema = {
        properties: {
            confirm: {
                description: `You are missing ${hasNoImage.length} files of the latest positive sightings. Do you want to download now? Y/n`,
                required: true
            },
          }
    }
    const confirmation = await prompt.getSync(schema).then(res=>res.confirm)

    if (confirmation!=="Y"){
        console.error("Will continue without downloading new files.")
    } else {
        let counter = 0
        for (const record of hasNoImage) {
            counter +=1
            const fileName = `${record.ID}.png`
            const options = {
                destination: path.join(IMAGE_PATH, fileName)
            }
            await storage.bucket(bucketName).file(record.PATH).download(options).catch(e=>{
                console.log(`Error! Could not download ${fileName}, File does not exist!`)
                removeFile(path.join(IMAGE_PATH, fileName))
            })
            console.log(`${counter} out of ${hasNoImage.length} images downloaded.`)
        }
    }

    // check which files have missing txt files
    const updatedFilesInImagePath = await fs.readdirSync(path.join(IMAGE_PATH))
    let textFilesInImagePath = updatedFilesInImagePath.map(i=>i.split(".")).filter(i=>i[1]==="txt")
    let updatedImageFilesInImagePath = updatedFilesInImagePath.map(i=>i.split(".")).filter(i=>i[1]==="png")

    // generate text files for images
    // text files names are <id>.txt
    //[category number] [object center in X] [object center in Y] [object width in X] [object width in Y]

    const recordsToMakeTxtFiles = DATABASE_RECORDS.filter(i=>updatedImageFilesInImagePath.map(f=>f[0]).indexOf(i.ID)>-1)

    if (argv['multi-class']) {
        console.log("MULTICLASS MODE ENABLED")
    }

    for (const record of recordsToMakeTxtFiles) {
        const fileName = `${record.ID}.txt`
        const yolo = convertFromCornersToYoloFormat(...record["boundingBox"])
        let category = undefined
        if (argv['multi-class']) {
            category = 0
        } else {
            category = 0
        }
        await fs.writeFileSync(path.join(IMAGE_PATH, fileName), `${category} ${yolo.objectCenterX} ${yolo.objectCenterY} ${yolo.objectWidthX} ${yolo.objectWidthY}`)
    }

    // create train and text txt files
    let TEST_PERCENTAGE = 30
    if (argv['test-percentage']) {
        TEST_PERCENTAGE = Math.round(parseFloat(argv['test-percentage']))
    }

    // split 
    const filesToAdd = updatedImageFilesInImagePath.filter(file=>DATABASE_RECORDS.map(i=>i.ID).indexOf(file[0])>-1).map(i=>path.join(IMAGE_RELATIVE_PATH, i.join(".")))
    
    let trainFiles = []
    let testFiles = []

    for (const file of filesToAdd) {
        const rnd = Math.random()
        if (rnd*100>TEST_PERCENTAGE){
            trainFiles.push(file)
        } else {
            testFiles.push(file)
        }
    }

    // writing to test and train files
    await fs.writeFileSync(path.join(DARKNET_PATH, "train.txt"), trainFiles.join("\n"))
    await fs.writeFileSync(path.join(DARKNET_PATH, "test.txt"), testFiles.join("\n"))

    console.log("Number of images in the training set: %s", trainFiles.length)
    console.log("Number of images in the test set: %s", testFiles.length)

}

main()