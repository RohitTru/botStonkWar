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

// Utility function to format numbers
function formatNumber(num) {
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(num);
}

// Format timestamp to relative time
function formatRelativeTime(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // difference in seconds

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
}

// Create a strategy card
function createStrategyCard(strategy) {
    const healthClass = {
        'Healthy': 'bg-green-100 text-green-800',
        'Error': 'bg-red-100 text-red-800',
        'Idle': 'bg-yellow-100 text-yellow-800',
        'Unknown': 'bg-gray-100 text-gray-800'
    }[strategy.metrics.health] || 'bg-gray-100 text-gray-800';

    return `
        <div class="strategy-card ${strategy.metrics.health === 'Healthy' ? 'active' : ''}">
            <div class="strategy-header">
                <div>
                    <h3 class="text-lg font-semibold text-gray-900">${strategy.name}</h3>
                    <span class="px-2 py-1 text-xs rounded-full ${healthClass}">${strategy.metrics.health}</span>
                </div>
                <div class="text-right">
                    <span class="text-sm text-gray-500">Last Run</span>
                    <p class="text-sm font-medium">${formatRelativeTime(strategy.metrics.last_run)}</p>
                </div>
            </div>
            
            <div class="strategy-description">
                <p>${strategy.description}</p>
            </div>
            
            <div class="metrics-section">
                <!-- Last Hour Performance -->
                <div class="metrics-block">
                    <div class="metrics-block-header">
                        <h4 class="metrics-title">Last Hour Performance</h4>
                        <span class="time-badge">Past 60 min</span>
                    </div>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <span class="metric-label">Recommendations</span>
                            <strong class="metric-value">${strategy.metrics.hourly.recommendations_generated}</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Success Rate</span>
                            <strong class="metric-value">${formatNumber(strategy.metrics.hourly.success_rate)}%</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Avg Confidence</span>
                            <strong class="metric-value">${formatNumber(strategy.metrics.hourly.avg_confidence * 100)}%</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Articles Processed</span>
                            <strong class="metric-value">${strategy.metrics.hourly.articles_processed}</strong>
                        </div>
                    </div>
                </div>
                
                <!-- Trading Signals -->
                <div class="metrics-block">
                    <div class="metrics-block-header">
                        <h4 class="metrics-title">Trading Signals</h4>
                        <span class="time-badge">Hourly / Total</span>
                    </div>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <span class="metric-label">Buy Signals</span>
                            <strong class="metric-value">${strategy.metrics.hourly.buy_signals}</strong>
                            <span class="metric-trend">Total: ${strategy.metrics.total_buy_signals}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Sell Signals</span>
                            <strong class="metric-value">${strategy.metrics.hourly.sell_signals}</strong>
                            <span class="metric-trend">Total: ${strategy.metrics.total_sell_signals}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Buy Confidence</span>
                            <strong class="metric-value">${formatNumber(strategy.metrics.hourly.avg_buy_confidence * 100)}%</strong>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Sell Confidence</span>
                            <strong class="metric-value">${formatNumber(strategy.metrics.hourly.avg_sell_confidence * 100)}%</strong>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="strategy-footer">
                <div class="footer-stats">
                    <span>Total Runs: ${strategy.metrics.total_runs}</span>
                    <span>All-time Success: ${formatNumber(strategy.metrics.all_time_success_rate)}%</span>
                    ${strategy.metrics.errors ? 
                        `<span class="text-red-500">Last Error: ${formatRelativeTime(strategy.metrics.last_error_time)}</span>` : 
                        ''}
                </div>
            </div>
        </div>
    `;
}

// Load and display strategies
async function loadStrategies() {
    try {
        const response = await fetch('/api/strategy-status');
        if (!response.ok) throw new Error('Failed to fetch strategies');
        
        const data = await response.json();
        const strategies = data.strategies || [];
        
        // Update counts
        document.getElementById('active-strategies-count').textContent = 
            `${strategies.filter(s => s.metrics.health === 'Healthy').length} Active`;
        document.getElementById('total-strategies-count').textContent = 
            `${strategies.length} Total`;
        
        // Update strategy carousel
        const carousel = document.getElementById('strategy-status');
        if (strategies.length === 0) {
            carousel.innerHTML = '<p class="text-gray-500">No strategies available</p>';
            return;
        }
        
        carousel.innerHTML = strategies
            .sort((a, b) => {
                // Sort by health status (Healthy first, then Idle, then Error)
                const healthOrder = { 'Healthy': 0, 'Idle': 1, 'Error': 2, 'Unknown': 3 };
                return healthOrder[a.metrics.health] - healthOrder[b.metrics.health];
            })
            .map(createStrategyCard)
            .join('');
            
    } catch (error) {
        console.error('Error loading strategies:', error);
        document.getElementById('strategy-status').innerHTML = 
            '<p class="text-red-500">Error loading strategies. Please try again later.</p>';
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadStrategies();
    // Refresh strategies every 30 seconds
    setInterval(loadStrategies, 30000);
}); 