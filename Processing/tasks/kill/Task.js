var TaskRunner = require('terminal-task-runner');
var logger = TaskRunner.logger;
var Shell = TaskRunner.shell

var Task = TaskRunner.Base.extend({
    id: 'killListeners',
    name: 'KILL ALL RUNNING PROCESSES',
    position: 100,
    run: function(cons) {
        new Shell(['pm2 stop all && pm2 delete all'], true).start().then(function() {
            cons();
        }, function(err) {
            cons(err);
        });
    }
});


module.exports = Task;