const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const fs = require('fs')
const moment = require('moment')

const header = [
    {id: 'time', title: 'WRITTEN_AT'},
    {id: 'timeUNIX', title: 'TIME_UNIX'},
    {id: 'timeISO', title: 'TIME_ISO'},
    {id: 'timeGPS', title: 'TIME_GPS'},
    {id: 'GPS_COORDS', title: 'GPS_COORDS'},
    {id: 'CAM', title: 'CAMERA_ID'},
    {id: 'PLATE', title: 'PLATE'},
    {id: 'PATH', title: 'PATH'},
    {id: 'ID', title: 'ID'}
]
// imageName = "ID="+str(uid)+"_CAM="+CAM_CONFIG[camId]['ref']+"_UNIX="+str(round(time.time()*1000))+".png"

if (process.argv.length<=2) {
    console.log("Must declare a path to the directory. Usage: " + __filename + " path/to/directory     - Exiting...")
    process.exit(-1)
}

const path = process.argv[2]

const writer = createCsvWriter({
    header,
    path: path+"/processed.csv",
    append: true
})

console.log(path)

fs.readdir(path, (err, items)=> {
    console.log(items)
    let rowsToWrite = []
    items&&items.filter(i=>i.split('.')[1]==="png").forEach((file)=>{
        const PATH = file
        const components = file.split(".")[0].split("_").map(i=>({key: i.split("=")[0], value: i.split("=")[1]})).reduce((obj,v)=>({...obj, [v.key]: v.value}), {})
        const ID = components["ID"]
        const CAM = components["CAM"]
        const PLATE = "NONE"
        const GPS_COORDS = ""
        const timeGPS = ""
        const timeISO = moment(parseInt(components["UNIX"])).toISOString()
        const timeUNIX = components["UNIX"]
        const time = components["UNIX"]
        rowsToWrite.push({time, timeUNIX, timeISO, timeGPS, GPS_COORDS, CAM, PLATE, PATH, ID})
    })
    writer.writeRecords(rowsToWrite)

    console.log("Produced file and saved in " + path + "as processed.csv")
})