const fs = require('fs-extra')
const config = require('./../config.json')

// With async/await:
async function example (src, dest) {
    try {
      await fs.remove(config.STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.RAW_STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.STAGED_STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.PROCESSED_STORE_PATH.slice(0, -1))
      console.log('Successfully reset store on server')
    } catch (err) {
      console.error(err)
    }
  }
  
  example()