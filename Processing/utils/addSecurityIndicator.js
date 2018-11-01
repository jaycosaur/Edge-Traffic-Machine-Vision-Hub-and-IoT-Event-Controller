const path = require('path')
const chalk = require('chalk')

const addChunkToPng = require('./addChunkToPng')

const PNG = require('png-js');
const sha256 = require('sha256')
 
const fileToSecure = path.join(__dirname, process.argv[2])
const ouputPath = path.join(__dirname, process.argv[2], ".secure")

addChunkToPng({}, fileToSecure, ouputPath, true, ()=>{
    console.log(chalk.cyan(`SECURITY INDICATOR WRITTEN TO FILE`))
})


