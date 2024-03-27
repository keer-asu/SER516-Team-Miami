document.addEventListener("DOMContentLoaded", function() {
    // Sample data for demonstration

    const days = [];
    const storyPointsData = [];

    // Calculate ratio of story points for each day
    const ratioData = storyPointsData


    // Chart.js configuration
    const ctx = document.getElementById('partial-work-done-chart').getContext('2d');
    const valueInProgressChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                label: 'Story Points Ratio',
                data: ratioData,
                backgroundColor: 'rgba(255, 99, 132, 0.6)', // Red color with opacity for the bars
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Ratio of Story Points' // Set the name for y-axis
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Days' // Set the name for x-axis
                    }
                }
            }
        }
    });



    // Chart.js configuration
    const bvBox = document.getElementById('BV-graph').getContext('2d');
    const bvInProgressChart = new Chart(bvBox, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                label: 'Bussiness Value Ratio',
                data: ratioData,
                backgroundColor: 'rgba(255, 99, 132, 0.6)', // Red color with opacity for the bars
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Ratio of Bussiness Value' // Set the name for y-axis
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Days' // Set the name for x-axis
                    }
                }
            }
        }
    });

    document.getElementById('loading').style.display = 'block';
    document.getElementById('loading2').style.display = 'block';
    fetch("/VIPC")
    .then(response => response.json())
    .then(data_points => {
        var labels = data_points.map(x => x.date);
        var work = data_points.map(x => x.user_story_points);
        var BV = data_points.map(x => x.BV);
        valueInProgressChart.data = {
            labels: labels,
            datasets: [{
                label: 'Story Points Ratio',
                data: work,
                backgroundColor: 'rgba(255, 99, 132, 0.6)', // Red color with opacity for the bars
                borderWidth: 1
            }]
        };

        bvInProgressChart.data = {
            labels: labels,
            datasets: [{
                label: 'Bussiness Value Ratio',
                data: BV,
                backgroundColor: 'rgba(255, 99, 132, 0.6)', // Red color with opacity for the bars
                borderWidth: 1
            }]
        };
        document.getElementById('loading').style.display = 'none';
        document.getElementById('loading2').style.display = 'none';
        valueInProgressChart.update();
        bvInProgressChart.update();
    })

});
