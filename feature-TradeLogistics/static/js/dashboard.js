// Function to update the performance chart
function updatePerformanceChart(data) {
    const traces = [];
    
    // Create a trace for each strategy
    for (const strategy of data.strategies) {
        traces.push({
            x: strategy.timestamps,
            y: strategy.performance,
            name: strategy.name,
            type: 'scatter',
            mode: 'lines',
            line: {
                width: 2,
                shape: 'spline'
            }
        });
    }

    const layout = {
        title: 'Strategy Performance Over Time',
        xaxis: {
            title: 'Time',
            showgrid: true,
            gridcolor: '#f3f4f6'
        },
        yaxis: {
            title: 'Performance (%)',
            showgrid: true,
            gridcolor: '#f3f4f6',
            tickformat: '.1f'
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        showlegend: true,
        legend: {
            x: 0,
            y: 1,
            bgcolor: 'rgba(255, 255, 255, 0.9)',
            bordercolor: '#e5e7eb',
            borderwidth: 1
        },
        margin: {
            l: 50,
            r: 20,
            t: 40,
            b: 50
        },
        hovermode: 'closest'
    };

    Plotly.newPlot('performance-chart', traces, layout, {
        responsive: true,
        displayModeBar: false
    });
}

// Function to fetch updated data
async function fetchDashboardData() {
    try {
        const response = await fetch('/api/dashboard-data');
        const data = await response.json();
        
        // Update performance chart
        updatePerformanceChart(data.performance);
        
        // Update strategy statuses
        updateStrategyStatuses(data.strategies);
        
        // Update metrics
        updateMetrics(data.metrics);
        
        // Update recommendations
        await loadRecommendations();
        
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

// Function to update strategy statuses
function updateStrategyStatuses(strategies) {
    const statusElements = document.querySelectorAll('[data-strategy-status]');
    statusElements.forEach(element => {
        const strategyId = element.dataset.strategyId;
        const strategy = strategies.find(s => s.id === strategyId);
        if (strategy) {
            element.textContent = strategy.status;
            element.className = `px-2 inline-flex text-xs leading-5 font-semibold rounded-full status-${strategy.status.toLowerCase()}`;
        }
    });
}

// Function to update metrics
function updateMetrics(metrics) {
    Object.entries(metrics).forEach(([key, value]) => {
        const element = document.querySelector(`[data-metric="${key}"]`);
        if (element) {
            element.textContent = value;
        }
    });
}

// Function to load and display recommendations
async function loadRecommendations() {
    try {
        const response = await fetch('/api/recommendations');
        const recommendations = await response.json();
        displayRecommendations(recommendations);
    } catch (error) {
        console.error('Error loading recommendations:', error);
    }
}

function displayRecommendations(recommendations) {
    const recommendationsList = document.getElementById('recommendations-list');
    if (!recommendationsList) return;

    recommendationsList.innerHTML = recommendations.map(rec => `
        <div class="recommendation-card card mb-3 ${rec.action} hover-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h5 class="card-title">${rec.symbol}</h5>
                        <h6 class="card-subtitle mb-2 text-${rec.action === 'buy' ? 'success' : 'danger'}">
                            ${rec.action.toUpperCase()}
                        </h6>
                    </div>
                    <span class="badge bg-${rec.timeframe === 'short_term' ? 'warning' : 'info'}">
                        ${rec.timeframe}
                    </span>
                </div>
                <p class="card-text">${rec.reasoning}</p>
                <div class="confidence-bar mb-2">
                    <div class="progress bg-${rec.action === 'buy' ? 'success' : 'danger'}" 
                         style="width: ${rec.confidence * 100}%"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">Confidence: ${(rec.confidence * 100).toFixed(1)}%</small>
                    <small class="text-muted">Strategy: ${rec.strategy_name}</small>
                </div>
            </div>
        </div>
    `).join('');
}

function filterRecommendations(action) {
    const recommendations = document.querySelectorAll('.recommendation-card');
    recommendations.forEach(rec => {
        if (action === 'all' || rec.classList.contains(action)) {
            rec.style.display = 'block';
        } else {
            rec.style.display = 'none';
        }
    });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Initial data fetch
    fetchDashboardData();
    
    // Set up periodic updates
    setInterval(fetchDashboardData, 30000); // Update every 30 seconds
}); 