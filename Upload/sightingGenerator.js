const sample = require('./sample.json')
const uuid = require('uuid/v4')

// one cam per sighting
// within X seconds
// possible plates

let sightingsQueue = []
let sightingsHash = {}

let data = sample

const cams = ['CAM1','CAM2','CAM3','CAM4','CAM5','CAM6','CAM7','CAM8','CAM9']

const camGroups = {
    far: ['CAM1','CAM4','CAM9'],
    truck: ['CAM2','CAM5','CAM7'],
    close: ['CAM3','CAM6','CAM8']
}

const farData = data.filter(i=>far.includes(i.CAM))
const truckData = data.filter(i=>truck.includes(i.CAM))
const closeData = data.filter(i=>close.includes(i.CAM))

let delayThreshold = 3000 // max 5 second delay
let minTriggerThreshold = 100

// assumption : cam 1, cam 4, cam 9 always first
// 2,5, 7 are second
// 3,6,8 last

const sightingTemplate = {
    firstTime: null,
    plates: [],
    linkedRecords: [],
    ...cams.reduce((a,b)=>({...a,[b]:null}),{})
}

const addNewSighting = () => {
    let id = uuid()
    sightingsQueue.push(id)
    sightingsHash = {
        ...sightingsHash,
        [id]: {
            ...sightingTemplate
        }
    }
    return id
}

const addToSighting = (id, record) => {
    sightingsHash = {
        ...sightingsHash,
        [id]: {
            ...sightingsHash[id],
            firstTime: (record.time<sightingsHash[id].firstTime||!sightingsHash[id].firstTime)?record.time:sightingsHash[id].firstTime,
            [record.CAM]: true,
            plates: [...sightingsHash[id].plates, record.PLATE],
            linkedRecords: [...sightingsHash[id].linkedRecords,record.ID]
        }
    }
}

// add first sighting
addNewSighting()

let sightingIndex = 0

sample.slice(0,1000).forEach((element,index) => {
    console.log(index)
    console.log(sightingsQueue.length)
    const pSID = sightingsQueue[sightingIndex-1]
    const cSID = sightingsQueue[sightingIndex]
    const nSID = sightingsQueue[sightingIndex+1]

    const previousSighting = pSID?sightingsHash[pSID]:null
    const currentSighting = cSID?sightingsHash[cSID]:null
    const nextSighting = nSID?sightingsHash[nSID]:null

    if (currentSighting.firstTime&&element.time-currentSighting.firstTime>delayThreshold){
        sightingIndex += 1
    }

    if (currentSighting[element.CAM]){
        if(!nextSighting){
            let id = addNewSighting()
            addToSighting(id, element)
        } else {
            addToSighting(nSID, element)
        }
    } else {
        if(!currentSighting.firstTime||element.time-currentSighting.firstTime<delayThreshold){
            addToSighting(cSID, element)
        } else {
            if(!nextSighting){
                let id = addNewSighting()
                addToSighting(id, element)
            } else {
                addToSighting(nSID, element)
            }
        }
    }
});

console.log(sightingsHash)
/* 
    if cam in sighting
        add to next

    if cam not in current sighting and under threshold
        add to current

    if cam not in current sighting and above threshold
        add to next
*/