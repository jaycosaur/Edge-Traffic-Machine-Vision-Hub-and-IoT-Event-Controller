const fs = require('fs-extra')
const config = require('./../config.json')
const axios = require('axios')

async function resetServerStore () {
    try {
      const STORE_PATH = config.STORE_PATH
      await fs.remove(STORE_PATH.slice(0, -1))
      await fs.ensureDir(STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.RAW_STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.STAGED_STORE_PATH.slice(0, -1))
      await fs.ensureDir(config.PROCESSED_STORE_PATH.slice(0, -1))
      await axios.post(config.SLACK_WEBHOOK_URL, {
        text: "Reset server store at site!",
        color: "#66ff66"
      })
      console.log('Successfully reset store on server')
    } catch (err) {
      console.error(err)
    }
  }
  
resetServerStore()