const bdConsistencyGraphConfig = {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Story Points',
            data: [],
            borderColor: 'rgba(255, 99, 132, 1)', // Red color for story points
            borderWidth: 2,
            fill: true
        }, {
            label: 'B.V. Points',
            data: [],
            borderColor: 'rgba(54, 162, 235, 1)', // Blue color for B.V. points
            borderWidth: 2,
            fill: true
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Points'
                }
            }
        }
    }
};


async function getGraohData(){
    console.log('Called');
    try{
        const response = await fetch('/bd-calculation');

        if(!response.ok) throw new Error('Failed fetch BD Graph Calculations!');

        const chartData =  await response.json();

        bdConsistencyGraphConfig.data.labels = chartData.x_axis.map(date => {
            const dateObj = new Date(date);
            return `${dateObj.getDate()} ${dateObj.toLocaleDateString('default', { month: 'short' })}`
        });

        bdConsistencyGraphConfig.data.datasets[0].data = chartData.story_points_projection;

        bdConsistencyGraphConfig.data.datasets[1].data = Object.values(chartData.bv_projection);

        const ctx = document.getElementById('graph').getContext('2d');
        const consistencyChart = new Chart(ctx, bdConsistencyGraphConfig);
    } catch(err) {
        console.log(err);
    }
}




document.addEventListener("DOMContentLoaded", () => {
    getGraohData();

    // Chart.js configuration
});
