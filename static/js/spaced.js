// Spaced repetition algorithm and visualization
document.addEventListener('DOMContentLoaded', function() {
    // Progress chart for spaced repetition
    const progressChart = document.getElementById('progress-chart');
    
    if (progressChart) {
        // We're using Chart.js for visualization
        // This assumes you've included Chart.js in your project
        try {
            const ctx = progressChart.getContext('2d');
            
            // Get data from the data attribute
            const reviewData = JSON.parse(progressChart.dataset.reviews || '[]');
            const successRateData = JSON.parse(progressChart.dataset.success || '[]');
            
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: reviewData.map((_, index) => `Day ${index + 1}`),
                    datasets: [
                        {
                            label: 'Reviews Completed',
                            data: reviewData,
                            backgroundColor: 'rgba(79, 70, 229, 0.2)',
                            borderColor: 'rgba(79, 70, 229, 1)',
                            borderWidth: 2,
                            tension: 0.3
                        },
                        {
                            label: 'Success Rate (%)',
                            data: successRateData,
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            borderColor: 'rgba(16, 185, 129, 1)',
                            borderWidth: 2,
                            tension: 0.3,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Reviews'
                            }
                        },
                        y1: {
                            beginAtZero: true,
                            max: 100,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Success Rate (%)'
                            },
                            grid: {
                                drawOnChartArea: false
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error rendering chart:', error);
            // Fallback to a simple text display if Chart.js isn't available
            progressChart.innerHTML = '<p>Chart visualization requires Chart.js library</p>';
        }
    }
    
    // Interval setting for spaced repetition
    const intervalSlider = document.getElementById('interval-slider');
    const intervalValue = document.getElementById('interval-value');
    
    if (intervalSlider && intervalValue) {
        intervalSlider.addEventListener('input', function() {
            // Update the displayed value
            const days = this.value;
            if (days === "1") {
                intervalValue.textContent = "1 day";
            } else {
                intervalValue.textContent = `${days} days`;
            }
        });
    }
    
    // Display of next review dates
    const reviewDateElements = document.querySelectorAll('.next-review-date');
    
    if (reviewDateElements.length) {
        reviewDateElements.forEach(element => {
            const timestamp = element.dataset.timestamp;
            if (timestamp) {
                const reviewDate = new Date(timestamp);
                const now = new Date();
                
                // Calculate difference in days
                const diffTime = reviewDate - now;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                if (diffDays < 0) {
                    element.innerHTML = '<span class="overdue">Overdue</span>';
                    element.closest('.flashcard-item').classList.add('overdue');
                } else if (diffDays === 0) {
                    element.innerHTML = '<span class="due-today">Due today</span>';
                    element.closest('.flashcard-item').classList.add('due-today');
                } else if (diffDays === 1) {
                    element.innerHTML = '<span class="due-soon">Due tomorrow</span>';
                    element.closest('.flashcard-item').classList.add('due-soon');
                } else {
                    element.textContent = `Due in ${diffDays} days`;
                }
            }
        });
    }
});
