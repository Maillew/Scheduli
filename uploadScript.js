//the problem occurs cuz we load in for the first time, we still have our previous session data
//currently, new data is only getting updated on the second refresh/render
document.addEventListener("DOMContentLoaded", function() {
    // Load the tasks from sessionStorage when the page loads for the first time
    clearTasksContainer();
    loadTasksFromFlask();
    // Add an event listener to the "Add Task" form
    document.getElementById("add-task-form").addEventListener("submit", function(event) {
        event.preventDefault();
        addTask();
    });
    console.log(JSON.parse(sessionStorage.getItem("due_dates")));
    
    document.getElementById("post-tasks-button").addEventListener("click", function(event) {
        event.preventDefault();
        postTasksToFlask();
    });
});

function loadTasksFromFlask(callback) {
    fetch('/get-data')
        .then(response => response.json())
        .then(data => {
            // Store the fetched data in session storage
            sessionStorage.setItem("due_dates", JSON.stringify(data));
            console.log("Flask data " + data.length)
            loadTasksFromSessionStorage();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
function clearTasksContainer() {
    const tasksContainer = document.getElementById("tasks-container");

    while (tasksContainer.firstChild) {
        tasksContainer.removeChild(tasksContainer.firstChild);
    }
}

function loadTasksFromSessionStorage() {//session data is getting ran before flask data
    const storedDueDates = sessionStorage.getItem("due_dates");
    if (storedDueDates) {
        const dueDates = JSON.parse(storedDueDates);
        console.log("Session data " +dueDates.length)
        clearTasksContainer()
        dueDates.forEach(function (task, index) {
            displayTask(task, index);
        });
    }
}


function displayTask(task, index) { // problem is that each time we are adding to the html, andn ot clearing it
    const tasksContainer = document.getElementById("tasks-container");
    const taskRow = document.createElement("div");
    taskRow.className = "task-row";
    taskRow.innerHTML = `
        <div id = "task">• ${task.date}: ${task.name} <a href="#" onclick="deleteTask(${index})">Delete</a></div>
    `;
    tasksContainer.appendChild(taskRow);
}

function addTask() {
    const date = document.getElementById("add-task-form").elements.date.value;
    const name = document.getElementById("add-task-form").elements.name.value;

    const task = { date, name };
    let tasks = JSON.parse(sessionStorage.getItem("due_dates")) || [];

    tasks.push(task);
    tasks.sort((a, b) => (a.date > b.date) ? 1 : -1);
    sessionStorage.setItem("due_dates", JSON.stringify(tasks));
    loadTasksFromSessionStorage();
    document.getElementById("add-task-form").reset();
}

function deleteTask(index) {
    let tasks = JSON.parse(sessionStorage.getItem("due_dates")) || [];
    tasks.splice(index, 1);
    sessionStorage.setItem("due_dates", JSON.stringify(tasks));
    loadTasksFromSessionStorage();
}

function postTasksToFlask() {
    const dueDates = JSON.parse(sessionStorage.getItem("due_dates"));

    fetch('/post', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ due_dates: dueDates })
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the server, if needed
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}