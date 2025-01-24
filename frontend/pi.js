const pieChartElement = document.getElementById('pieChart');

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const pieCtx = pieChartElement.getContext('2d');
            const pieChart = new Chart(pieCtx, {
                type: 'pie',
                data: {
                    labels: ['Save fuels', 'Energy Efficiency', 'Accident free travel', 'Time Saving', 'Cost Savings'],
                    datasets: [{
                        data: [30, 20, 10, 30, 10],
                        backgroundColor: [
                            'rgba(117, 7, 31, 0.93)',
                            'rgba(2, 67, 22, 0.78)',
                            'rgba(117, 86, 7, 0.81)',
                            'rgba(6, 116, 116, 0.73)',
                            'rgba(36, 5, 98, 0.72)'
                        ],
                        borderColor: [
                            'rgb(69, 10, 23)',
                            'rgb(5, 45, 72)',
                            'rgb(62, 46, 5)',
                            'rgb(8, 68, 68)',
                            'rgb(33, 11, 78)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                font: {
                                    size: 14,
                                    weight: 'bold',
                                },
                                boxWidth: 20,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            bodyFont: {
                                size: 12
                            },
                            callbacks: {
                                label: function(tooltipItem) {
                                    return `${tooltipItem.label}: ${tooltipItem.raw}%`;
                                }
                            }
                        }
                    },
                    layout: {
                        padding: {
                            left: 10,
                            right: 10,
                            top: 10,
                            bottom: 10
                        }
                    }
                }
            });
           
            observer.unobserve(pieChartElement);
        }
    });
}, { threshold: 0.5 }); 


observer.observe(pieChartElement);
