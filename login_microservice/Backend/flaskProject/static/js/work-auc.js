const work_auc_chart_config = {
    type: 'bar',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Work AUC',
                data: [],
                // borderColor: '#ff8fa7',
                // backgroundColor: '#ff8fa7',
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Sprints',
                    font: { size: 15 },
                },
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'AUC in percentage',
                    font: { size: 15 },
                },

            }
        },
    }
}

$(function () {
    $.ajax({
        url: '/work-auc-data',
        type: 'GET',
        success: function (response) {
            work_auc_chart_config.data.labels = response.x_axis
            work_auc_chart_config.data.datasets[0].data = response.work_auc_by_sprint_order;

            const work_auc_chart = document.getElementById('work_auc_chart').getContext('2d');
            new Chart(work_auc_chart, work_auc_chart_config);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log(XMLHttpRequest.status)
            console.log(textStatus)
        }
    })
})

