const extract = require('png-chunks-extract')
const text = require('png-chunk-text')
const path = require('path')
const fs = require('fs')
const chalk = require('chalk')

const PNG = require('png-js');
const sha256 = require('sha256')
 
const buffer = fs.readFileSync(path.join(__dirname, process.argv[2]))
const chunks = extract(buffer)

let newSecInd = undefined
 
const textChunks = chunks.filter(function (chunk) {
  return chunk.name === 'tEXt'
}).map(function (chunk) {
  return text.decode(chunk.data)
})

console.log(chalk.yellow('META DATA STORED ON IMAGE:\n'))

textChunks.map(chunk=>console.log(chalk.blue(`${chunk.keyword}: ${chunk.text}`)))

const metaSecInd = textChunks.map(i=>i.keyword).indexOf("security_indicator")>-1?textChunks[textChunks.map(i=>i.keyword).indexOf("security_indicator")].text:null

console.log(chalk.cyan(`\n\nSECURITY INDICATOR IN META DATA: ${metaSecInd}`))


new PNG(buffer).decode((pixels)=>{
    newSecInd = sha256(pixels.toString('utf8'))
    console.log(chalk.cyan(`SECURITY INDICATOR ON IMAGE: ${newSecInd}\n\n`))
    console.log(newSecInd===metaSecInd?chalk.green.bold(`SECURITY INDICATORS MATCH, PASS`):chalk.red.bold(`SECURITY INDICATORS DO NOT MATCH, FAIL`))
})



