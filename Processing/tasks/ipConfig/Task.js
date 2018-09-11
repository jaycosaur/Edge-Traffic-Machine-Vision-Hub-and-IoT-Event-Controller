var TaskRunner = require('terminal-task-runner');
var logger = TaskRunner.logger;



var Task = TaskRunner.Base.extend({
    id: 'ipconfig',
    name: 'Camera IP configuration',
    position: 101,
    run: function(cons) {
        this.prompt([{
            type: 'input',
            name: 'option',
            message: 'Are you sure you want to erase the data? This is permanent. Y/N',
            validate: function(pass) {
                return !!pass;
            }
        }], function(res) {
                logger.info(res.option==="Y"?"You deleted all the data!":"You did not delete the data.");
                cons();
            });
    }
});


module.exports = Task;