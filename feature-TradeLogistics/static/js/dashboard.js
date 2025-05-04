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

// Utility functions for formatting
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatPercent(num) {
    if (num === null || num === undefined) return 'N/A';
    return num.toFixed(1) + '%';
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function getHealthClass(health) {
    switch (health?.toLowerCase()) {
        case 'healthy': return 'bg-green-100 text-green-800';
        case 'idle': return 'bg-yellow-100 text-yellow-800';
        case 'error': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// Create a strategy card
function createStrategyCard(strategy) {
    const metrics = strategy.metrics || {};
    const hourly = metrics.hourly || {};
    // All-time metrics
    const totalRuns = formatNumber(metrics.total_runs || 0);
    const totalArticles = formatNumber(metrics.total_articles_processed || 0);
    const totalRecs = formatNumber(metrics.total_recommendations || 0);
    const totalBuy = formatNumber(metrics.total_buy_signals || 0);
    const totalSell = formatNumber(metrics.total_sell_signals || 0);
    const allTimeSuccess = formatPercent(metrics.all_time_success_rate || 0);
    const lastRun = formatTimestamp(metrics.last_run);
    const errorCount = metrics.error_count || 0;
    const lastError = metrics.errors;
    const lastErrorTime = metrics.last_error_time ? formatTimestamp(metrics.last_error_time) : null;
    // Hourly metrics
    const hourlyRecs = formatNumber(hourly.recommendations_generated || 0);
    const hourlyArticles = formatNumber(hourly.articles_processed || 0);
    const hourlyBuy = formatNumber(hourly.buy_signals || 0);
    const hourlySell = formatNumber(hourly.sell_signals || 0);
    const hourlySuccess = formatPercent(hourly.success_rate || 0);
    const avgConfidence = formatPercent(hourly.avg_confidence * 100 || 0);
    const avgBuyConfidence = formatPercent(hourly.avg_buy_confidence * 100 || 0);
    const avgSellConfidence = formatPercent(hourly.avg_sell_confidence * 100 || 0);
    const execTime = hourly.execution_time_ms || 0;
    return `
        <div class="strategy-card bg-white rounded-lg shadow-md p-6 mb-4 w-96 flex-shrink-0">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h3 class="text-xl font-semibold">${strategy.name}</h3>
                    <p class="text-sm text-gray-600 mb-2">${strategy.description}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="px-2 py-1 text-sm rounded-full ${getHealthClass(metrics.health)}">
                        ${metrics.health || 'Unknown'}
                    </span>
                    <label class="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" class="sr-only peer" 
                               ${strategy.active ? 'checked' : ''}
                               onchange="toggleStrategy('${strategy.name}', this.checked)">
                        <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 
                                  peer-focus:ring-blue-300 rounded-full peer 
                                  peer-checked:after:translate-x-full peer-checked:after:border-white 
                                  after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
                                  after:bg-white after:border-gray-300 after:border after:rounded-full 
                                  after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600">
                        </div>
                    </label>
                </div>
            </div>
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-500 mb-2">Last Hour</h4>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div>Recs: <span class="font-semibold">${hourlyRecs}</span></div>
                    <div>Articles: <span class="font-semibold">${hourlyArticles}</span></div>
                    <div>Buy: <span class="font-semibold">${hourlyBuy}</span></div>
                    <div>Sell: <span class="font-semibold">${hourlySell}</span></div>
                    <div>Success: <span class="font-semibold">${hourlySuccess}</span></div>
                    <div>Avg Conf: <span class="font-semibold">${avgConfidence}</span></div>
                    <div>Avg Buy Conf: <span class="font-semibold">${avgBuyConfidence}</span></div>
                    <div>Avg Sell Conf: <span class="font-semibold">${avgSellConfidence}</span></div>
                    <div>Exec Time: <span class="font-semibold">${execTime}ms</span></div>
                </div>
            </div>
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-500 mb-2">All Time</h4>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div>Runs: <span class="font-semibold">${totalRuns}</span></div>
                    <div>Articles: <span class="font-semibold">${totalArticles}</span></div>
                    <div>Recs: <span class="font-semibold">${totalRecs}</span></div>
                    <div>Buy: <span class="font-semibold">${totalBuy}</span></div>
                    <div>Sell: <span class="font-semibold">${totalSell}</span></div>
                    <div>Success: <span class="font-semibold">${allTimeSuccess}</span></div>
                    <div>Last Run: <span class="font-semibold">${lastRun}</span></div>
                </div>
            </div>
            ${errorCount > 0 || lastError ? `
                <div class="mt-2 p-2 bg-red-50 rounded-lg">
                    <h4 class="text-xs font-medium text-red-800 mb-1">Recent Error</h4>
                    <p class="text-xs text-red-600">${lastError || ''}</p>
                    <p class="text-xxs text-red-500 mt-1">Occurred at: ${lastErrorTime || ''}</p>
                </div>
            ` : ''}
        </div>
    `;
}

// Function to toggle strategy activation
async function toggleStrategy(strategyName, active) {
    try {
        const response = await fetch('/api/strategy-activation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_name: strategyName,
                active: active
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update strategy activation');
        }
        
        // Refresh strategies after toggling
        loadStrategies();
        
    } catch (error) {
        console.error('Error toggling strategy:', error);
        // Revert the checkbox state
        const checkbox = document.querySelector(`input[type="checkbox"][onchange*="${strategyName}"]`);
        if (checkbox) {
            checkbox.checked = !active;
        }
    }
}

// Load strategies function
async function loadStrategies() {
    const strategiesContainer = document.getElementById('strategies-container');
    const loadingElement = document.getElementById('loading-strategies');
    const errorElement = document.getElementById('error-loading-strategies');
    
    if (!strategiesContainer || !loadingElement || !errorElement) {
        console.error('Required DOM elements not found');
        return;
    }
    
    try {
        loadingElement.classList.remove('hidden');
        errorElement.classList.add('hidden');
        
        // Fetch dashboard data for metrics
        const dashboardResp = await fetch('/api/dashboard-data');
        const dashboardData = await dashboardResp.json();
        const metrics = dashboardData.metrics || {};
        const strategies = dashboardData.strategies || [];
        
        // Update active strategies count
        const activeCount = strategies.filter(s => s.active).length;
        const activeCountElement = document.getElementById('active-strategies-count');
        if (activeCountElement) {
            activeCountElement.textContent = activeCount;
        }
        // Update recommendations in last hour
        const recsLastHourElement = document.getElementById('recs-last-hour');
        if (recsLastHourElement) {
            recsLastHourElement.textContent = metrics.recommendations_last_hour || 0;
        }
        // Update total recommendations
        const totalRecsElement = document.getElementById('total-recommendations');
        if (totalRecsElement) {
            totalRecsElement.textContent = formatNumber(metrics.total_recommendations || 0);
        }
        // Render strategy cards
        strategiesContainer.innerHTML = strategies.map(createStrategyCard).join('');
        
    } catch (error) {
        console.error('Error loading strategies:', error);
        errorElement.classList.remove('hidden');
        errorElement.textContent = 'Error loading strategies. Please try again.';
    } finally {
        loadingElement.classList.add('hidden');
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadStrategies();
    // Refresh strategies every minute
    setInterval(loadStrategies, 60000);
}); 