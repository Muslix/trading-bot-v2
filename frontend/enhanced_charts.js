/**
 * Enhanced Charts Module for Crypto Trading Bot
 * 
 * Features:
 * - Interactive arbitrage heatmaps
 * - Real-time candlestick charts
 * - Correlation analysis
 * - Performance attribution charts
 * - Risk/return scatter plots
 */

class EnhancedCharts {
    constructor() {
        this.charts = new Map();
        this.colorSchemes = {
            profit: ['#27AE60', '#2ECC71', '#58D68D', '#82E0AA'],
            loss: ['#E74C3C', '#EC7063', '#F1948A', '#F5B7B1'],
            neutral: ['#95A5A6', '#BDC3C7', '#D5DBDB', '#EAEDED'],
            arbitrage: ['#3498DB', '#5DADE2', '#85C1E9', '#AED6F1']
        };
    }
    
    /**
     * Create enhanced arbitrage heatmap
     */
    createArbitrageHeatmap(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Prepare heatmap data
        const exchanges = [...new Set([
            ...data.map(d => d.buy_exchange),
            ...data.map(d => d.sell_exchange)
        ])];
        
        const symbols = [...new Set(data.map(d => d.symbol))];
        
        // Create heatmap HTML
        container.innerHTML = `
            <div class="heatmap-container">
                <div class="heatmap-header">
                    <h5>🔥 Arbitrage Opportunities Heatmap</h5>
                    <small class="text-muted">Profit potential across exchanges</small>
                </div>
                <div class="heatmap-grid" id="${containerId}-grid"></div>
                <div class="heatmap-legend">
                    <span class="legend-item">
                        <span class="legend-color" style="background: #27AE60;"></span>
                        High Profit (>3%)
                    </span>
                    <span class="legend-item">
                        <span class="legend-color" style="background: #F39C12;"></span>
                        Medium Profit (1-3%)
                    </span>
                    <span class="legend-item">
                        <span class="legend-color" style="background: #95A5A6;"></span>
                        Low/No Profit (<1%)
                    </span>
                </div>
            </div>
        `;
        
        // Build grid
        const grid = document.getElementById(`${containerId}-grid`);
        
        // Create exchange pair matrix
        const matrix = {};
        exchanges.forEach(buyEx => {
            matrix[buyEx] = {};
            exchanges.forEach(sellEx => {
                if (buyEx !== sellEx) {
                    matrix[buyEx][sellEx] = {
                        opportunities: data.filter(d => d.buy_exchange === buyEx && d.sell_exchange === sellEx),
                        maxProfit: 0,
                        count: 0
                    };
                    
                    const opportunities = matrix[buyEx][sellEx].opportunities;
                    matrix[buyEx][sellEx].count = opportunities.length;
                    matrix[buyEx][sellEx].maxProfit = opportunities.length > 0 
                        ? Math.max(...opportunities.map(o => o.profit_percentage || 0))
                        : 0;
                }
            });
        });
        
        // Create grid HTML
        let gridHTML = '<div class="heatmap-row"><div class="heatmap-cell header"></div>';
        exchanges.forEach(ex => {
            gridHTML += `<div class="heatmap-cell header">${ex}</div>`;
        });
        gridHTML += '</div>';
        
        exchanges.forEach(buyEx => {
            gridHTML += `<div class="heatmap-row"><div class="heatmap-cell header">${buyEx}</div>`;
            exchanges.forEach(sellEx => {
                if (buyEx === sellEx) {
                    gridHTML += '<div class="heatmap-cell disabled">-</div>';
                } else {
                    const cellData = matrix[buyEx][sellEx];
                    const profit = cellData.maxProfit;
                    const count = cellData.count;
                    
                    let colorClass = 'low';
                    if (profit > 3) colorClass = 'high';
                    else if (profit > 1) colorClass = 'medium';
                    
                    gridHTML += `
                        <div class="heatmap-cell ${colorClass}" 
                             data-buy="${buyEx}" data-sell="${sellEx}"
                             data-profit="${profit.toFixed(2)}" data-count="${count}"
                             title="${count} opportunities, max ${profit.toFixed(2)}%">
                            <div class="cell-profit">${profit > 0 ? profit.toFixed(1) + '%' : '-'}</div>
                            <div class="cell-count">${count}</div>
                        </div>
                    `;
                }
            });
            gridHTML += '</div>';
        });
        
        grid.innerHTML = gridHTML;
        
        // Add click handlers
        grid.querySelectorAll('.heatmap-cell:not(.header):not(.disabled)').forEach(cell => {
            cell.addEventListener('click', (e) => {
                const buyEx = e.currentTarget.dataset.buy;
                const sellEx = e.currentTarget.dataset.sell;
                const opportunities = matrix[buyEx][sellEx].opportunities;
                this.showOpportunityDetails(opportunities, buyEx, sellEx);
            });
        });
    }
    
    /**
     * Create real-time price chart with candlesticks
     */
    createRealTimePriceChart(containerId, symbol, data) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Destroy existing chart
        if (this.charts.has(containerId)) {
            this.charts.get(containerId).destroy();
        }
        
        const ctx = container.getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.timestamps || [],
                datasets: [{
                    label: `${symbol} Price`,
                    data: data.prices || [],
                    borderColor: '#3498DB',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    title: {
                        display: true,
                        text: `${symbol} Real-Time Price`,
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                return `$${context.parsed.y.toFixed(4)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Price (USD)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    /**
     * Create correlation matrix heatmap
     */
    createCorrelationMatrix(containerId, correlationData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const symbols = Object.keys(correlationData);
        
        container.innerHTML = `
            <div class="correlation-container">
                <div class="correlation-header">
                    <h5>🔗 Asset Correlation Matrix</h5>
                    <small class="text-muted">Price correlation between assets</small>
                </div>
                <div class="correlation-grid" id="${containerId}-grid"></div>
                <div class="correlation-legend">
                    <span class="legend-item">
                        <span class="legend-color" style="background: #E74C3C;"></span>
                        Strong Negative (-1.0)
                    </span>
                    <span class="legend-item">
                        <span class="legend-color" style="background: #95A5A6;"></span>
                        No Correlation (0.0)
                    </span>
                    <span class="legend-item">
                        <span class="legend-color" style="background: #27AE60;"></span>
                        Strong Positive (+1.0)
                    </span>
                </div>
            </div>
        `;
        
        const grid = document.getElementById(`${containerId}-grid`);
        
        // Create correlation matrix HTML
        let matrixHTML = '<div class="correlation-row"><div class="correlation-cell header"></div>';
        symbols.forEach(symbol => {
            matrixHTML += `<div class="correlation-cell header">${symbol}</div>`;
        });
        matrixHTML += '</div>';
        
        symbols.forEach(symbol1 => {
            matrixHTML += `<div class="correlation-row"><div class="correlation-cell header">${symbol1}</div>`;
            symbols.forEach(symbol2 => {
                const correlation = correlationData[symbol1]?.[symbol2] || 0;
                const intensity = Math.abs(correlation);
                const isPositive = correlation >= 0;
                
                let colorClass = '';
                if (intensity > 0.7) colorClass = isPositive ? 'strong-positive' : 'strong-negative';
                else if (intensity > 0.3) colorClass = isPositive ? 'medium-positive' : 'medium-negative';
                else colorClass = 'neutral';
                
                matrixHTML += `
                    <div class="correlation-cell ${colorClass}" 
                         data-correlation="${correlation.toFixed(3)}"
                         title="${symbol1} vs ${symbol2}: ${correlation.toFixed(3)}">
                        ${correlation.toFixed(2)}
                    </div>
                `;
            });
            matrixHTML += '</div>';
        });
        
        grid.innerHTML = matrixHTML;
    }
    
    /**
     * Create risk/return scatter plot
     */
    createRiskReturnChart(containerId, performanceData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Destroy existing chart
        if (this.charts.has(containerId)) {
            this.charts.get(containerId).destroy();
        }
        
        const ctx = container.getContext('2d');
        
        // Prepare scatter data
        const scatterData = performanceData.map(item => ({
            x: item.volatility || 0,
            y: item.annual_return || 0,
            symbol: item.symbol,
            sharpe: item.sharpe_ratio || 0
        }));
        
        const chart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Assets',
                    data: scatterData,
                    backgroundColor: function(context) {
                        const sharpe = context.parsed.sharpe || 0;
                        if (sharpe > 1) return '#27AE60';
                        if (sharpe > 0.5) return '#F39C12';
                        return '#E74C3C';
                    },
                    borderColor: '#2C3E50',
                    borderWidth: 2,
                    pointRadius: 8,
                    pointHoverRadius: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Risk vs Return Analysis',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            title: function(context) {
                                return context[0].raw.symbol;
                            },
                            label: function(context) {
                                const data = context.raw;
                                return [
                                    `Return: ${data.y.toFixed(2)}%`,
                                    `Risk: ${data.x.toFixed(2)}%`,
                                    `Sharpe: ${data.sharpe.toFixed(3)}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Volatility (Risk) %'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Annual Return %'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    /**
     * Create performance attribution donut chart
     */
    createPerformanceDonut(containerId, attributionData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        // Destroy existing chart
        if (this.charts.has(containerId)) {
            this.charts.get(containerId).destroy();
        }
        
        const ctx = container.getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: attributionData.map(item => item.label),
                datasets: [{
                    data: attributionData.map(item => item.value),
                    backgroundColor: [
                        '#3498DB', '#27AE60', '#F39C12', '#E74C3C', 
                        '#9B59B6', '#1ABC9C', '#34495E', '#16A085'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Performance Attribution',
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const percentage = ((context.parsed / context.dataset.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                                return `${context.label}: ${percentage}%`;
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(containerId, chart);
        return chart;
    }
    
    /**
     * Update chart with new data (for real-time updates)
     */
    updateChart(containerId, newData) {
        const chart = this.charts.get(containerId);
        if (!chart) return;
        
        // Update data based on chart type
        if (chart.config.type === 'line') {
            chart.data.labels.push(newData.timestamp);
            chart.data.datasets[0].data.push(newData.price);
            
            // Keep only last 50 points for performance
            if (chart.data.labels.length > 50) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
        }
        
        chart.update('none'); // No animation for real-time updates
    }
    
    /**
     * Show opportunity details modal
     */
    showOpportunityDetails(opportunities, buyExchange, sellExchange) {
        if (opportunities.length === 0) return;
        
        const modal = document.createElement('div');
        modal.className = 'opportunity-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h5>🔄 ${buyExchange} → ${sellExchange} Opportunities</h5>
                    <button class="close-btn" onclick="this.closest('.opportunity-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    ${opportunities.map((opp, i) => `
                        <div class="opportunity-item">
                            <div class="opp-symbol">${opp.symbol}</div>
                            <div class="opp-profit ${opp.profit_percentage > 3 ? 'high' : opp.profit_percentage > 1 ? 'medium' : 'low'}">
                                ${opp.profit_percentage.toFixed(2)}%
                            </div>
                            <div class="opp-details">
                                Buy: $${opp.buy_price?.toFixed(4)} | Sell: $${opp.sell_price?.toFixed(4)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    /**
     * Destroy all charts
     */
    destroyAll() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
}

// Export for use in main application
window.EnhancedCharts = EnhancedCharts;