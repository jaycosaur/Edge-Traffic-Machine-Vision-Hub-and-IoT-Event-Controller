var TaskRunner = require('terminal-task-runner');
var logger = TaskRunner.logger;
var Shell = TaskRunner.shell

var Task = TaskRunner.Base.extend({
    id: 'startAutoBackup',
    name: '*CRITICAL* Start Auto Backup Before Starting Any Scripts (PM2 Process)',
    position: 1,
    run: function(cons) {
        //Task has to be asynchronous, otherwise, you won't receive the finish/error event
        new Shell(['pm2 start ./autoBackup.js --name "auto-backup"'], true).start().then(function() {
            cons();
        }, function(err) {
            cons(err);
        });
    }
});


module.exports = Task;