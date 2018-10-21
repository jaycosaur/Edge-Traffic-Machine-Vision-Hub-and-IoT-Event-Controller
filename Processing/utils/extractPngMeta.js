const extract = require('png-chunks-extract')
const text = require('png-chunk-text')
const path = require('path')
const fs = require('fs')
 
const buffer = fs.readFileSync(path.join(__dirname, process.argv[2]))
const chunks = extract(buffer)
 
const textChunks = chunks.filter(function (chunk) {
  return chunk.name === 'tEXt'
}).map(function (chunk) {
  return text.decode(chunk.data)
})

console.log(textChunks)