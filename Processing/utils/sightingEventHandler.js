const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const chalk = require('chalk');

const header = [
    {id: 'time', title: 'WRITTEN_AT'},
    {id: 'timeUNIX', title: 'TIME_UNIX'},
    {id: 'timeISO', title: 'TIME_ISO'},
    {id: 'timeGPS', title: 'TIME_GPS'},
    {id: 'GPS_COORDS', title: 'GPS_COORDS'},
    {id: 'CAM', title: 'CAMERA_ID'},
    {id: 'PLATE', title: 'PLATE'},
    {id: 'PACKAGE_ID', title: 'PACKAGE_ID'},
    {id: 'PATH', title: 'PATH'},
    {id: 'ID', title: 'ID'},
]
 
class writerClass {
    constructor(attrs){
        this.path = attrs.path
        this.writer = createCsvWriter({
            path: attrs.path,
            header,
            append: true
        })
    }
    
    write(record){
        this.writer.writeRecords([{
            time: Date.now(),
            ...record,
        }])       // returns a promise
            .then(() => {
                console.log(chalk.magenta(`${Date.now()} => ${Object.keys(record).map(key=>`${key}=${record[key]}`)}`));
            });
    }
}

module.exports = writerClass