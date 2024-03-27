document.addEventListener('DOMContentLoaded', function() {
    
    // Data for the chart
    var data = {
        labels: [], // Sample labels for tasks
        datasets: [{
            label: 'Task Cycle Time',
            data: [], // Sample data for Task Cycle Time
            backgroundColor: 'rgba(54, 162, 235, 0.2)', // Blue color for Task Cycle Time
            borderColor: 'rgba(54, 162, 235, 1)', // Border color for Task Cycle Time
            borderWidth: 1
        }]
    };

    // Configuration options for the chart
    var options = {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Days' 
                }
            }
        }
    };

    // Get the canvas element
    var ctx = document.getElementById('myChart').getContext('2d');

    // Create the bar chart
    var myChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: options
    });



    document.getElementById('task_selection').addEventListener('submit', sendData);

    sendData({ preventDefault: function(){} });

    function sendData(event) {
        event.preventDefault();
        document.getElementById('loading').style.display = 'block';
        var task_ids = document.getElementById('task_ids').value;
        var task_ids_list = task_ids.split(',').map(Number);
        console.log(task_ids_list);
        fetch('/cycle-time-graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ closed_tasks_ids: task_ids_list}),
        })
        .then(response => response.json())
        .then(task_id_cycle_time => {
            var labels = task_id_cycle_time.map(x => x.task_id);
            var data = task_id_cycle_time.map(x => x.cycle_time);
            myChart.data = {
                labels: labels,
                datasets: [{
                    label: 'Task Cycle Time',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            }
            myChart.update();
            document.getElementById('loading').style.display = 'none';});
            console.log(myChart.data);
        
        }  
            
});



