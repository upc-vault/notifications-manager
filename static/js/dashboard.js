/**
 * Dashboard JavaScript - ML Learning Visualization
 */

const API = 'http://localhost:8080';
let templateChart, channelChart;

function log(message, type = 'info') {
    const logDiv = document.getElementById('log');
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logDiv.insertBefore(entry, logDiv.firstChild);
    console.log(message);
}

async function refreshData() {
    try {
        log('Fetching model statistics...', 'info');
        const response = await fetch(`${API}/api/v1/models/stats`);
        const data = await response.json();
        
        updateTemplateChart(data.template_statistics);
        updateChannelChart(data.channel_statistics);
        updateStats(data);
        
        log('✓ Statistics updated', 'success');
    } catch (error) {
        log('✗ Failed to fetch statistics: ' + error.message, 'error');
    }
}

function updateTemplateChart(templates) {
    const ctx = document.getElementById('templateChart').getContext('2d');
    
    const labels = Object.keys(templates);
    const engagementData = labels.map(t => (templates[t].avg_engagement * 100).toFixed(1));
    const successData = labels.map(t => (templates[t].success_rate * 100).toFixed(1));
    
    if (templateChart) templateChart.destroy();
    
    templateChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Engagement %',
                    data: engagementData,
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Success Rate %',
                    data: successData,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Update template stats
    const statsDiv = document.getElementById('templateStats');
    statsDiv.innerHTML = labels.map(t => `
        <div class="stat-box">
            <div class="stat-label">${t}</div>
            <div class="stat-value">${templates[t].count}</div>
            <div style="font-size: 11px; color: #666;">pulls</div>
        </div>
    `).join('');
}

function updateChannelChart(channels) {
    const ctx = document.getElementById('channelChart').getContext('2d');
    
    const labels = Object.keys(channels);
    const successData = labels.map(c => (channels[c].success_rate * 100).toFixed(1));
    
    if (channelChart) channelChart.destroy();
    
    channelChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Success Rate %',
                data: successData,
                backgroundColor: [
                    'rgba(37, 211, 102, 0.7)',
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(241, 196, 15, 0.7)',
                    'rgba(231, 76, 60, 0.7)',
                    'rgba(155, 89, 182, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });

    // Update channel stats
    const statsDiv = document.getElementById('channelStats');
    statsDiv.innerHTML = labels.map(c => `
        <div class="stat-box">
            <div class="stat-label">${c}</div>
            <div class="stat-value">${channels[c].total_selections}</div>
            <div style="font-size: 11px; color: #666;">selections</div>
        </div>
    `).join('');
}

function updateStats(data) {
    const templates = data.template_statistics;
    const channels = data.channel_statistics;
    
    const totalPulls = Object.values(templates).reduce((sum, t) => sum + t.count, 0);
    const totalSelections = Object.values(channels).reduce((sum, c) => sum + c.total_selections, 0);
    const avgEngagement = Object.values(templates).reduce((sum, t) => sum + t.avg_engagement, 0) / Object.keys(templates).length;
    const avgSuccess = Object.values(channels).reduce((sum, c) => sum + c.success_rate, 0) / Object.keys(channels).length;

    document.getElementById('overallStats').innerHTML = `
        <div class="stat-box">
            <div class="stat-label">Total Template Pulls</div>
            <div class="stat-value">${totalPulls}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Total Channel Selections</div>
            <div class="stat-value">${totalSelections}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Avg Engagement</div>
            <div class="stat-value">${(avgEngagement * 100).toFixed(1)}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Avg Success Rate</div>
            <div class="stat-value">${(avgSuccess * 100).toFixed(1)}%</div>
        </div>
    `;
}

async function simulateFeedback() {
    const templates = ['urgent', 'friendly', 'formal', 'concise', 'promotional', 'personalized', 'informative', 'security', 'reward', 'reminder'];
    const channels = ['whatsapp', 'sms', 'email', 'push', 'webpush'];
    
    const template = templates[Math.floor(Math.random() * templates.length)];
    const channel = channels[Math.floor(Math.random() * channels.length)];
    const success = Math.random() > 0.3;
    const engagement = success ? Math.random() * 0.5 + 0.5 : Math.random() * 0.3;

    try {
        log(`Simulating feedback: ${template} + ${channel} (success=${success})`, 'info');
        
        const response = await fetch(`${API}/api/v1/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                notification_id: 'sim_' + Date.now(),
                template: template,
                channel: channel,
                success: success,
                engagement: engagement
            })
        });

        if (response.ok) {
            log(`✓ Feedback processed: ${template} engagement=${engagement.toFixed(2)}`, 'success');
            setTimeout(refreshData, 500);
        } else {
            const error = await response.json();
            log(`✗ Feedback failed: ${error.message}`, 'error');
        }
    } catch (error) {
        log(`✗ Error: ${error.message}`, 'error');
    }
}

async function simulateBatch() {
    log('Starting batch simulation (10 feedbacks)...', 'info');
    for (let i = 0; i < 10; i++) {
        await simulateFeedback();
        await new Promise(resolve => setTimeout(resolve, 200));
    }
    log('✓ Batch simulation complete', 'success');
}

// Initial load
refreshData();

// Auto-refresh every 10 seconds
setInterval(refreshData, 10000);
