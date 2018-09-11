var openalpr = require ("node-openalpr");

openalpr.Start();

const extractPlateFromImage = (id, path, cb) => {
    openalpr.IdentifyLicense (path, function (error, output) {
        var results = output.results;
        cb(results.length>0?results[0].plate:null, output.processing_time_ms, id, output)
        if (id == 349) {
            openalpr.Stop();
        }
    })
}

module.exports = extractPlateFromImage
