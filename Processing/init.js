var TaskRunner = require('terminal-task-runner');
 
TaskRunner.createMenu({
    title: 'One Task System Controller',
    subtitle: 'Initiate System Actions',
    taskDir: "./tasks",
    exitTxt: "EXIT (THIS DOES NOT END PROCESSES)",
    taskList: [
        "viewer",
        "ipConfig",
        "setJumbo",
        "start-post-process",
        "start-streaming",
        "restart-streaming",
        "stop-streaming",
        "kill",
        "exports",
        "erase"
    ]
});