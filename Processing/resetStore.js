const fs = require('fs-extra')
const config = require('./../config.json')

const options = {
  mode: 0o2775
}

// With async/await:
async function example (src, dest) {
    try {
      const STORE_PATH = config.STORE_PATH
      await fs.remove(STORE_PATH.slice(0, -1))
      await fs.ensureDir(STORE_PATH.slice(0, -1),options)
      await fs.ensureDir(config.RAW_STORE_PATH.slice(0, -1),options)
      await fs.ensureDir(config.STAGED_STORE_PATH.slice(0, -1),options)
      await fs.ensureDir(config.PROCESSED_STORE_PATH.slice(0, -1),options)
      console.log('Successfully reset store on server')
    } catch (err) {
      console.error(err)
    }
  }
  
  example()