const graphConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Partial Work Done',
                data: [],
                borderColor: 'orange',
                fill: true
            },
            {
                label: 'Total Work Done',
                data: [],
                borderColor: 'white',
                fill: true
            },
            {
                label: 'Business Value',
                data: [],
                borderColor: 'red',
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

async function getGraphData(){
    try{
        const partialWorkDoneChartResponse = await fetch('/partial-work-done-chart');

        if(!partialWorkDoneChartResponse.ok) throw new Error('Failed to fetch json data!');

        const partialWorkDoneChartData =  await partialWorkDoneChartResponse.json();

        graphConfig.data.labels = partialWorkDoneChartData.x_axis.map(date => {
            const dateObj = new Date(date);
            return `${dateObj.getDate()} ${dateObj.toLocaleDateString('default', { month: 'short' })}`
        });

        graphConfig.data.datasets[0].data = partialWorkDoneChartData.actual_projection;

        // ---------------------------
        
        const totalWorkDoneChartResponse = await fetch('/total-work-done-chart');

        if(!totalWorkDoneChartResponse.ok) throw new Error('Failed to fetch json data!');

        const totalWorkDoneChartData =  await totalWorkDoneChartResponse.json();

        graphConfig.data.datasets[1].data = totalWorkDoneChartData.actual_projection;
        
        // ---------------------------
        
        const businessValueChartResponse = await fetch('/burndown-bv-data');

        if(!businessValueChartResponse.ok) throw new Error('Failed to fetch json data!');

        const businessValueChartData =  await businessValueChartResponse.json();

        graphConfig.data.datasets[2].data = businessValueChartData[0].map(entry => entry[1]);
        
        const graph = document.getElementById('graph').getContext('2d');
        new Chart(graph, graphConfig);

        // const businessValueChart = document.getElementById('business-value-chart').getContext('2d');
        // new Chart(businessValueChart, partialWorkDoneChartConfig);
    } catch (err) {
        console.log(err);
    }
}

// $(function () {
//     $.ajax({
//         url: '/burndown-bv-data',
//         type: 'GET',
//         success: function (response) {
//             new Chart($('#business-value-chart'), {
//                 type: 'line',
//                 data: {
//                     labels: response[0].map(entry => entry[0]),
//                     datasets: [
//                         {
//                             label: 'Actual Business Value Delivered by Date',
//                             data: response[0].map(entry => entry[1]),
//                             borderColor: '#ff0000',
//                             backgroundColor: '#ff008c',
//                         },
//                         {
//                             label: 'Ideal Business Value Delivered by Date',
//                             data: response[1].map(entry => entry[1]),
//                             borderColor: '#ffc800',
//                             backgroundColor: '#ffc800',
//                         }
//                     ]
//                 },
//                 options: {
//                     responsive: true,
//                     scales: {
//                         x: {
//                             title: {
//                                 display: true,
//                                 text: 'Date',
//                                 font: { size: 15 },
//                             },
//                         },
//                         y: {
//                             beginAtZero: true,
//                             title: {
//                                 display: true,
//                                 text: 'BV',
//                                 font: { size: 15 },
//                             },

//                         }
//                     },
//                 }
//             })
//         },
//         error: function (XMLHttpRequest, textStatus, errorThrown) {
//             console.log(XMLHttpRequest.status)
//             console.log(textStatus)
//         }
//     })
// })


getGraphData();