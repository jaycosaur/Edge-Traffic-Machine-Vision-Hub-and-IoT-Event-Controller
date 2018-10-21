const fs = require('fs-extra')
const config = require('./../config.json')
const axios = require('axios')

async function resetServerCache () {
    try {
      const CACHE_PATH = config.PROCESSED_STORE_PATH
      await fs.remove(CACHE_PATH.slice(0, -1))
      await fs.ensureDir(CACHE_PATH.slice(0, -1))
      await axios.post(config.SLACK_WEBHOOK_URL, {
        text: "Reset server cache at site!",
        color: "#66ff66"
      })
      console.log('Successfully reset cache on server')
    } catch (err) {
      console.error(err)
    }
  }
  
resetServerCache()