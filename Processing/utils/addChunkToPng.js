const extract = require('png-chunks-extract')
const encode = require('png-chunks-encode')
const text = require('png-chunk-text')
const fs = require('fs')
const PNG = require('png-js');
const sha256 = require('sha256')

const encoder = (keyvalue, currentPath, newPath, addIndicator, callback) => {
    fs.readFile(currentPath, (err, buffer) => {
        new PNG(buffer).decode((pixels)=>{
            if (addIndicator){
                let timestart = new Date.now()
                console.log('starting ....')
                securityIndicator = sha256(pixels.toString('utf8'))
                console.log("HASH TOOK: ", Math.round(Date.now()-timestart))
                keyvalue = {
                    ...keyvalue,
                    "security_indicator": securityIndicator
                }
            }
            const chunks = extract(buffer)
            Object.keys(keyvalue).forEach(key=>{
                chunks.splice(-1, 0, text.encode(key, keyvalue[key]))
            })
            fs.writeFile(newPath, new Buffer(encode(chunks)),
                (err) => {
                    if (err) console.log(err);
                    callback()
                }
            )
        })
    })
}

module.exports = encoder
