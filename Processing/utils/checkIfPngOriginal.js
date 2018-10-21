const extract = require('png-chunks-extract')
const text = require('png-chunk-text')
const path = require('path')
const fs = require('fs')

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

console.log('META DATA STORED ON IMAGE:')

textChunks.map(chunk=>console.log(`${chunk.keyword}: ${chunk.text}`))

console.log(textChunks.map(i=>i[0]))

const metaSecInd = textChunks.map(i=>i[0]).indexOf("security_indicator")>-1?textChunks[textChunks.map(i=>i[0]).indexOf("security_indicator")][1]:null

console.log(`SECURITY INDICATOR IN META DATA: ${metaSecInd}`)


new PNG(buffer).decode((pixels)=>{
    newSecInd = sha256(pixels.toString('utf8'))
    console.log(`SECURITY INDICATOR ON IMAGE: ${newSecInd}`)
    console.log(newSecInd===metaSecInd?`SECURITY INDICATORS MATCH, PASS`:`SECURITY INDICATORS DO NOT MATCH, FAIL`)
})



