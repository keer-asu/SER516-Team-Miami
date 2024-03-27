function generateColors(n){
    const colorsSet = new Set();
    const newColor = () => "#" + Math.floor(Math.random() * 16777215).toString(16)

    while(colorsSet.size < n) {
        const randomColor = newColor();
        if(colorsSet.has(randomColor)) continue;
        colorsSet.add(randomColor);
    }

    return colorsSet.values()
}

const partialWorkDoneChartConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: []
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
        datasets: []
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

const businessValueDoneChartConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: []
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

// const graphConfig = {
//     type: 'line',
//     data: {
//         labels: [],
//         datasets: []
//     },
//     options: {
//         responsive: true,
//         scales: {
//             yAxes: [{
//                 ticks: {
//                     beginAtZero: true // Ensure the y-axis starts at 0
//                 },
//                 scaleLabel: {
//                     display: true,
//                     labelString: 'User Story Points'
//                 }
//             }],
//             xAxes: [{
//                 scaleLabel: {
//                     display: true,
//                     labelString: 'Days'
//                 }
//             }]
//         }
//     }
// };

async function getGraphData(){
    try{
        // Colors set
        const generatedColors = generateColors(Object.keys(data_to_plot).length * 3);

        // Date check and plot x - axis
        const totalDays = [];

        for(const sprintNum in data_to_plot){
            const sprint = data_to_plot[sprintNum];
            const daysCount = sprint.partial_work_done.x_axis.length;
            const pwd = sprint.partial_work_done;
            const twd = sprint.total_work_done;
            const bv = sprint.business_value;

            // debugger
            partialWorkDoneChartConfig.data.datasets.push({
                label: `Sprint ${sprintNum}`,
                data: pwd.actual_projection,
                borderColor: generatedColors.next().value,
                fill: true
            });

            totalWorkDoneChartConfig.data.datasets.push({
                label: `Sprint ${sprintNum}`,
                data: twd.actual_projection,
                borderColor: generatedColors.next().value,
                fill: true
            });


            businessValueDoneChartConfig.data.datasets.push({
                label: `Sprint ${sprintNum}`,
                data: (typeof bv === 'object')? Object.values(bv).sort((a, b) => b - a) : [],
                borderColor: generatedColors.next().value,
                fill: true
            });

            totalDays.push(daysCount);
        }

        const maxDays = Math.max(...totalDays);
        const labels = [...Array(maxDays)].map((_, i) => `Day ${++i}`)
        
        partialWorkDoneChartConfig.data.labels = labels;
        totalWorkDoneChartConfig.data.labels = labels;
        businessValueDoneChartConfig.data.labels = labels;
        
        const partialWorkDoneGraphContainer = document.getElementById('partial-work-done-chart').getContext('2d');
        new Chart(partialWorkDoneGraphContainer, partialWorkDoneChartConfig);
        
        const totalWorkDoneGraphContainer = document.getElementById("total-work-done-chart").getContext('2d');
        new Chart(totalWorkDoneGraphContainer, totalWorkDoneChartConfig);
        
        const businessValueDoneGraphContainer = document.getElementById("business-value-chart").getContext('2d');
        new Chart(businessValueDoneGraphContainer, businessValueDoneChartConfig);
    } catch (err) {
        console.log(err);
    }
}

getGraphData();