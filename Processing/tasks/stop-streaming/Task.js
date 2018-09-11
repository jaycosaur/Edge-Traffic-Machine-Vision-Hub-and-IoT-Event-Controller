var TaskRunner = require('terminal-task-runner');
var logger = TaskRunner.logger;
var Shell = TaskRunner.shell



var Task = TaskRunner.Base.extend({
    id: 'stopStreaming',
    name: 'Stop Camera Capture and Streaming',
    position: 1,
    run: function(cons) {
        //Task has to be asynchronous, otherwise, you won't receive the finish/error event
        new Shell(['pm2 stop "vision-main" && pm2 remove "vision-main"'], true).start().then(function() {
            cons();
        }, function(err) {
            cons(err);
        });
    }
});


module.exports = Task;