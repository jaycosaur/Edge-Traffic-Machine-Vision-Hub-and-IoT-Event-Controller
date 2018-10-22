// Imports the Google Cloud client library
const Firestore = require('@google-cloud/firestore');
const jsonToCSV = require('json-to-csv');
const moment = require('moment')
const projectId = "onetask-tfnsw-web"
// Creates a client

const firestore = new Firestore({
    projectId: projectId,
    keyFilename: process.env.gcloudkeypath,
  });

firestore.settings({
    timestampsInSnapshots: true
})

const d = new Date()
const fileName = `csvDump/${moment().format("LLLL")}.csv`;

const main = async () => { 
    const getDump = await firestore.collection('records').where('isProcessed',"==",true).get().then(querySnapshot=>{
        let results = []
        querySnapshot.forEach(doc=> {
            const dat = doc.data()
            results.push({
                ID: dat.ID,
                TIME: moment(dat['timeISO']).format("LLLL"),
                ANGLE: dat.ANGLE,
                CAMERA: dat.CAM,
                IS_REVIEWED: dat.isReviewed,
                IS_REVIEWED_POSITIVE_SIGHTING: dat.isReviewedPositiveSighting,
                POSITIVE_PROCESED: dat.isPositiveSighting,
                IS_FLAGGED: dat.isFlagged,
                IS_TRUCK: dat.isTruck,
                LICENCE_PLATE: dat.licencePlate,
                FLASH_CONFIDENCE: dat.sightingConfidence4K,
                NON_FLASH_CONFIDENCE: dat.sightingConfidenceColor,
                VEHICLE_TYPE_REVIEW: dat.vehicleType,
                SIGHTING_CLASS: dat["sightingClass"], 
                PROCESSED_BY: dat.processedBy,
                PROCESSED_ON:  moment(dat['processedOn']).format("LLLL"),
                REVIEWED_BY: dat.reviewedBy,
                REVIEWED_ON: dat['reviewedOn']?moment(dat['reviewedOn']).format("LLLL"):""
            })
        })
        return results
    })
    console.log(getDump.length)
    jsonToCSV(getDump, fileName)
        .then(() => {
            console.log("COMPELTE!: ", getDump.length)
        })
        .catch(error => {
        // handle error
        })

}

main()