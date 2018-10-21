const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const chalk = require('chalk');

const header = [
    {id: 'time', title: 'TIME'},
    {id: 'message', title: 'message'},
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
            message: record
        }])       // returns a promise
            .then(() => {
                //console.log(chalk.green(`${Date.now()} => ${record}`));
            });
    }
}

module.exports = writerClass