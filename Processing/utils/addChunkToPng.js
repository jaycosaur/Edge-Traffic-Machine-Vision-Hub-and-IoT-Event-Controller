const extract = require('png-chunks-extract')
const encode = require('png-chunks-encode')
const text = require('png-chunk-text')
const fs = require('fs')
const PNG = require('png-js');
const sha256 = require('sha256')

const encoder = (keyvalue, currentPath, newPath, callback) => {
    fs.readFile(currentPath, (err, buffer) => {
        new PNG(buffer).decode((pixels)=>{
            console.log(pixels)
            securityIndicator = sha256("12345678910")
            const chunks = extract(buffer)
            Object.keys(keyvalue).forEach(key=>{
                chunks.splice(-1, 0, text.encode(key, keyvalue[key]))
            })
            chunks.splice(-1, 0, text.encode("security_indicator", securityIndicator))
            fs.writeFile(newPath, new Buffer(encode(chunks)),
                (err) => {
                    if (err) throw err;
                    callback()
                }
            )
        })
    })
}

module.exports = encoder
