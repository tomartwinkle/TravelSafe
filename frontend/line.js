const lineCtx = document.getElementById('lineChart').getContext('2d');
const lineChart = new Chart(lineCtx, {
    type: 'line',
    data: {
        labels: ['January', 'February', 'March', 'April', 'May', 'June'], 
        datasets: [
            {
                label: 'Travel Time',
                data: [500, 700, 600, 800, 750, 900],
                borderColor: 'rgb(16, 228, 72)',
                backgroundColor: 'rgba(16, 228, 72, 0.2)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            },
            {
                label: 'Travel Volume',
                data: [1000, 1000, 1000, 1000, 1000, 1000],
                borderColor: 'rgb(222, 17, 61)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            }
        ]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label}: ${context.raw}`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Amount ()'
                },
                grid: {
                    color: 'rgba(200, 200, 200, 0.5)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Months'
                }
            }
        }
    }
});



