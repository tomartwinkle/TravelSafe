const ctx = document.getElementById('spendingChart').getContext('2d');
const spendingChart = new Chart(ctx, {
  type: 'pie',
  data: {
    labels: ['Food', 'Rent', 'Entertainment', 'Savings', 'Miscellaneous'],
    datasets: [{
      data: [15000, 20000, 5000, 8000, 2000],
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      }
    }
  }
});

const progressBars = document.querySelectorAll('.progress');
progressBars.forEach(bar => {
  const width = bar.style.width;
  bar.style.width = '0';
  setTimeout(() => bar.style.width = width, 500);
});

