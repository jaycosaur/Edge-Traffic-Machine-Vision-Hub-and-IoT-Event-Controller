var sha256 = require('sha256')
var ex = require('exiv2');

a = sha256.x2("onetask")

const newTags = {
    "Exif.Photo.UserComment" : `securityindicator=${a}`,
  }

ex.setImageTags('./test.jpg', newTags, function(err){
    if (err) {
      console.error(err);
    } else {
      console.log("setImageTags complete..");
      ex.getImageTags('./test.jpg', function(err, tags) {
        console.log(tags)
      });
    }
  });

