const partialWorkDoneChartConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Ideal Values',
                data: [],
                borderColor: 'green',
                fill: true
            },
            {
                label: 'Actual Values',
                data: [],
                borderColor: 'blue',
                fill: true
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true // Ensure the y-axis starts at 0
                },
                scaleLabel: {
                    display: true,
                    labelString: 'User Story Points'
                }
            }],
            xAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'Days'
                }
            }]
        }
    }
};

const totalWorkDoneChartConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Actual Values',
                data: [],
                borderColor: 'blue',
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero: true // Ensure the y-axis starts at 0
                },
                scaleLabel: {
                    display: true,
                    labelString: 'User Story Points'
                }
            }],
            xAxes: [{
                scaleLabel: {
                    display: true,
                    labelString: 'Days'
                }
            }]
        }
    }
};

async function getGraphData(){
    try{
        const partialWorkDoneChartResponse = await fetch('/partial-work-done-chart');

        if(!partialWorkDoneChartResponse.ok) throw new Error('Failed to fetch json data!');

        const partialWorkDoneChartData =  await partialWorkDoneChartResponse.json();

        partialWorkDoneChartConfig.data.labels = partialWorkDoneChartData.x_axis.map(date => {
            const dateObj = new Date(date);
            return `${dateObj.getDate()} ${dateObj.toLocaleDateString('default', { month: 'short' })}`
        });

        partialWorkDoneChartConfig.data.datasets[0].data = partialWorkDoneChartData.ideal_projection;

        partialWorkDoneChartConfig.data.datasets[1].data = partialWorkDoneChartData.actual_projection;

        // ---------------------------
        
        const totalWorkDoneChartResponse = await fetch('/total-work-done-chart');

        if(!totalWorkDoneChartResponse.ok) throw new Error('Failed to fetch json data!');

        const totalWorkDoneChartData =  await totalWorkDoneChartResponse.json();

        totalWorkDoneChartConfig.data.labels = totalWorkDoneChartData.x_axis.map(date => {
            const dateObj = new Date(date);
            return `${dateObj.getDate()} ${dateObj.toLocaleDateString('default', { month: 'short' })}`
        });

        totalWorkDoneChartConfig.data.datasets[0].data = totalWorkDoneChartData.actual_projection;
        
        // ---------------------------
        
        
        const partialWorkDoneChart = document.getElementById('partial-work-done-chart').getContext('2d');
        new Chart(partialWorkDoneChart, partialWorkDoneChartConfig);

        const totalWorkDoneChart = document.getElementById('total-work-done-chart').getContext('2d');
        new Chart(totalWorkDoneChart, totalWorkDoneChartConfig);

        // const businessValueChart = document.getElementById('business-value-chart').getContext('2d');
        // new Chart(businessValueChart, partialWorkDoneChartConfig);
    } catch (err) {
        console.log(err);
    }
}

getGraphData();

