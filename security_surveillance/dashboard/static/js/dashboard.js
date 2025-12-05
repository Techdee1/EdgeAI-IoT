// ============================================
// Edge AI Dashboard - JavaScript Controller
// ============================================

// Global state
let currentMode = 'security';
let websocket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let charts = {};

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Edge AI Dashboard initializing...');
    
    // Initialize UI
    initModeSwitcher();
    initVideoStream();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Load initial data
    loadSecurityData();
    loadAgricultureData();
    
    // Set up periodic updates
    setInterval(updateDashboard, 5000); // Update every 5 seconds
    
    // Initialize event listeners
    initEventListeners();
    
    console.log('✅ Dashboard initialized');
});

// ============================================
// Mode Switching
// ============================================
function initModeSwitcher() {
    const securityBtn = document.getElementById('securityModeBtn');
    const agricultureBtn = document.getElementById('agricultureModeBtn');
    
    securityBtn.addEventListener('click', () => switchMode('security'));
    agricultureBtn.addEventListener('click', () => switchMode('agriculture'));
}

function switchMode(mode) {
    currentMode = mode;
    
    // Update button states
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`${mode}ModeBtn`).classList.add('active');
    
    // Update dashboard visibility
    document.querySelectorAll('.dashboard-mode').forEach(dashboard => {
        dashboard.classList.remove('active');
    });
    document.getElementById(`${mode}Dashboard`).classList.add('active');
    
    console.log(`📊 Switched to ${mode} mode`);
}

// ============================================
// WebSocket Connection
// ============================================
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    
    console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
    
    try {
        websocket = new WebSocket(wsUrl);
        
        websocket.onopen = () => {
            console.log('✅ WebSocket connected');
            reconnectAttempts = 0;
            updateSystemStatus('online');
            
            // Send initial ping
            websocket.send(JSON.stringify({ type: 'ping' }));
        };
        
        websocket.onmessage = (event) => {
            handleWebSocketMessage(JSON.parse(event.data));
        };
        
        websocket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            updateSystemStatus('error');
        };
        
        websocket.onclose = () => {
            console.log('🔌 WebSocket disconnected');
            updateSystemStatus('offline');
            
            // Attempt reconnection
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`🔄 Reconnecting... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
                setTimeout(connectWebSocket, 3000);
            }
        };
        
        // Keep-alive ping
        setInterval(() => {
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
        
    } catch (error) {
        console.error('❌ Failed to create WebSocket:', error);
        updateSystemStatus('error');
    }
}

function handleWebSocketMessage(message) {
    const { type, data } = message;
    
    switch (type) {
        case 'connected':
            console.log('📡 WebSocket connection confirmed');
            break;
            
        case 'detection':
            handleDetectionUpdate(data);
            break;
            
        case 'sensor_update':
            handleSensorUpdate(data);
            break;
            
        case 'alert':
            handleAlertUpdate(data);
            break;
            
        case 'system_status':
            handleSystemStatusUpdate(data);
            break;
            
        case 'pong':
            // Keep-alive response
            break;
            
        default:
            console.log('Unknown WebSocket message type:', type);
    }
}

function handleDetectionUpdate(data) {
    // Update people count
    if (data.count !== undefined) {
        document.getElementById('peopleCount').textContent = data.count;
    }
    
    // Reload detections list
    loadRecentDetections();
}

function handleSensorUpdate(data) {
    // Update sensor displays
    updateSensorDisplay(data);
}

function handleAlertUpdate(data) {
    // Add alert to list
    prependAlert(data);
}

function handleSystemStatusUpdate(data) {
    console.log('System status update:', data);
}

// ============================================
// Video Streaming
// ============================================
function initVideoStream() {
    const qualitySelect = document.getElementById('qualitySelect');
    const snapshotBtn = document.getElementById('snapshotBtn');
    const streamImg = document.getElementById('liveStream');
    
    function updateStream() {
        const quality = qualitySelect.value;
        streamImg.src = `/api/security/stream?quality=${quality}&t=${Date.now()}`;
    }
    
    qualitySelect.addEventListener('change', updateStream);
    snapshotBtn.addEventListener('click', takeSnapshot);
    
    // Start stream
    updateStream();
    
    // Handle stream errors
    streamImg.onerror = () => {
        console.warn('Stream error, retrying...');
        setTimeout(updateStream, 5000);
    };
}

async function takeSnapshot() {
    try {
        const response = await fetch('/api/security/snapshot');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // Download snapshot
        const a = document.createElement('a');
        a.href = url;
        a.download = `snapshot_${new Date().toISOString()}.jpg`;
        a.click();
        
        console.log('📸 Snapshot captured');
    } catch (error) {
        console.error('Failed to take snapshot:', error);
    }
}

// ============================================
// Security Dashboard Data Loading
// ============================================
async function loadSecurityData() {
    await Promise.all([
        loadSecurityStats(),
        loadRecentDetections(),
        loadZoneStatistics(),
        loadRecordings()
    ]);
}

async function loadSecurityStats() {
    try {
        const response = await fetch('/api/security/stats');
        const data = await response.json();
        
        document.getElementById('totalDetections').textContent = data.total_detections || 0;
        document.getElementById('systemEvents').textContent = data.system_events || 0;
        document.getElementById('recordingsCount').textContent = data.storage_files || 0;
        
        // Get people count separately
        const peopleResponse = await fetch('/api/security/people/count');
        const peopleData = await peopleResponse.json();
        document.getElementById('peopleCount').textContent = peopleData.current_count || 0;
        
    } catch (error) {
        console.error('Failed to load security stats:', error);
    }
}

async function loadRecentDetections() {
    try {
        const response = await fetch('/api/security/detections?limit=20');
        const data = await response.json();
        
        const container = document.getElementById('detectionsList');
        
        if (data.detections && data.detections.length > 0) {
            container.innerHTML = data.detections.map(detection => `
                <div class="detection-item">
                    <div class="detection-info">
                        <h4>Person Detected</h4>
                        <p>${new Date(detection.timestamp).toLocaleString()}</p>
                        ${detection.zone_name ? `<p>Zone: ${detection.zone_name}</p>` : ''}
                    </div>
                    <div class="detection-badge">
                        ${(detection.confidence * 100).toFixed(0)}%
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-search"></i>
                    <p>No recent detections</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load detections:', error);
    }
}

async function loadZoneStatistics() {
    try {
        const period = document.getElementById('zonePeriod')?.value || 7;
        const response = await fetch(`/api/security/zones?days=${period}`);
        const data = await response.json();
        
        if (data.zones && data.zones.length > 0) {
            renderZoneChart(data.zones);
        }
    } catch (error) {
        console.error('Failed to load zone statistics:', error);
    }
}

async function loadRecordings() {
    try {
        const sort = document.getElementById('recordingSort')?.value || 'newest';
        const response = await fetch(`/api/security/recordings?sort=${sort}&limit=10`);
        const data = await response.json();
        
        const container = document.getElementById('recordingsList');
        
        if (data.recordings && data.recordings.length > 0) {
            container.innerHTML = data.recordings.map(rec => `
                <div class="recording-item">
                    <div class="recording-header">
                        <span class="recording-name">${rec.filename}</span>
                        <span class="recording-size">${rec.size_mb} MB</span>
                    </div>
                    <div class="recording-meta">
                        ${new Date(rec.created).toLocaleString()}
                    </div>
                    <div class="recording-actions">
                        <button class="btn-sm" onclick="playRecording('${rec.filename}')">
                            <i class="fas fa-play"></i> Play
                        </button>
                        <button class="btn-sm" onclick="downloadRecording('${rec.filename}')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-video-slash"></i>
                    <p>No recordings available</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load recordings:', error);
    }
}

function playRecording(filename) {
    window.open(`/api/security/recording/${filename}`, '_blank');
}

function downloadRecording(filename) {
    const a = document.createElement('a');
    a.href = `/api/security/recording/${filename}`;
    a.download = filename;
    a.click();
}

// ============================================
// Agriculture Dashboard Data Loading
// ============================================
async function loadAgricultureData() {
    await Promise.all([
        loadSensorData(),
        loadSensorHistory(),
        loadIrrigationStatus(),
        loadAgricultureAlerts()
    ]);
}

async function loadSensorData() {
    try {
        const response = await fetch('/api/agriculture/sensors');
        const data = await response.json();
        
        if (data.sensors) {
            // Update stat cards
            const sensors = data.sensors;
            document.getElementById('soilMoisture').textContent = 
                sensors.soil_moisture?.value?.toFixed(1) || '--';
            document.getElementById('temperature').textContent = 
                sensors.air_temperature?.value?.toFixed(1) || '--';
            document.getElementById('humidity').textContent = 
                sensors.air_humidity?.value?.toFixed(1) || '--';
            document.getElementById('lightLevel').textContent = 
                sensors.light_intensity?.value?.toFixed(0) || '--';
            
            // Update sensor readings list
            renderSensorReadings(sensors);
        }
    } catch (error) {
        console.error('Failed to load sensor data:', error);
    }
}

function renderSensorReadings(sensors) {
    const container = document.getElementById('sensorReadings');
    
    if (!sensors || Object.keys(sensors).length === 0) {
        container.innerHTML = `
            <div class="no-data">
                <i class="fas fa-plug"></i>
                <p>No sensor data available</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = Object.entries(sensors).map(([name, sensor]) => `
        <div class="sensor-item">
            <div>
                <div class="sensor-name">${formatSensorName(name)}</div>
                <small style="color: var(--text-muted);">${sensor.last_updated ? new Date(sensor.last_updated).toLocaleTimeString() : ''}</small>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span class="sensor-value">${sensor.value} ${sensor.unit}</span>
                <span class="sensor-status ${sensor.status}">${sensor.status}</span>
            </div>
        </div>
    `).join('');
}

function formatSensorName(name) {
    return name.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

async function loadSensorHistory() {
    try {
        const sensorType = document.getElementById('sensorType')?.value;
        const hours = document.getElementById('historyPeriod')?.value || 24;
        
        const response = await fetch(`/api/agriculture/history?sensor=${sensorType}&hours=${hours}`);
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            renderSensorChart(data.history, sensorType);
        }
    } catch (error) {
        console.error('Failed to load sensor history:', error);
    }
}

async function loadIrrigationStatus() {
    try {
        const response = await fetch('/api/agriculture/irrigation/status');
        const data = await response.json();
        
        document.getElementById('pumpStatus').textContent = 
            data.pump_active ? 'Running' : 'Standby';
        document.getElementById('irrigationMode').textContent = 
            data.mode.charAt(0).toUpperCase() + data.mode.slice(1);
        document.getElementById('waterToday').textContent = 
            `${data.total_today?.toFixed(1) || 0} L`;
        document.getElementById('lastIrrigation').textContent = 
            data.last_irrigation ? new Date(data.last_irrigation).toLocaleString() : '--';
            
    } catch (error) {
        console.error('Failed to load irrigation status:', error);
    }
}

async function loadAgricultureAlerts() {
    try {
        const response = await fetch('/api/agriculture/alerts?limit=10');
        const data = await response.json();
        
        const container = document.getElementById('alertsList');
        
        if (data.alerts && data.alerts.length > 0) {
            container.innerHTML = data.alerts.map(alert => `
                <div class="alert-item ${alert.type}">
                    <div class="alert-header">
                        <span class="alert-type">${alert.type.toUpperCase()}</span>
                        <span class="alert-time">${new Date(alert.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-check-circle"></i>
                    <p>No active alerts</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load alerts:', error);
    }
}

function prependAlert(alert) {
    const container = document.getElementById('alertsList');
    const alertHTML = `
        <div class="alert-item ${alert.type}">
            <div class="alert-header">
                <span class="alert-type">${alert.type.toUpperCase()}</span>
                <span class="alert-time">${new Date(alert.timestamp).toLocaleString()}</span>
            </div>
            <div class="alert-message">${alert.message}</div>
        </div>
    `;
    
    // Remove no-data message if exists
    const noData = container.querySelector('.no-data');
    if (noData) noData.remove();
    
    container.insertAdjacentHTML('afterbegin', alertHTML);
}

// ============================================
// Irrigation Control
// ============================================
async function controlIrrigation(action, duration = null) {
    try {
        let url = `/api/agriculture/irrigation/control?action=${action}`;
        if (duration) url += `&duration=${duration}`;
        
        const response = await fetch(url, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Irrigation ${action} successful`);
            await loadIrrigationStatus();
        }
    } catch (error) {
        console.error('Failed to control irrigation:', error);
    }
}

// ============================================
// Chart Rendering
// ============================================
function renderZoneChart(zones) {
    const ctx = document.getElementById('zoneChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.zoneChart) {
        charts.zoneChart.destroy();
    }
    
    charts.zoneChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: zones.map(z => z.zone_name),
            datasets: [{
                label: 'Detections',
                data: zones.map(z => z.detection_count),
                backgroundColor: 'rgba(37, 99, 235, 0.6)',
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

function renderSensorChart(history, sensorType) {
    const ctx = document.getElementById('sensorChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.sensorChart) {
        charts.sensorChart.destroy();
    }
    
    charts.sensorChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: history.map(h => new Date(h.timestamp).toLocaleTimeString()),
            datasets: [{
                label: formatSensorName(sensorType),
                data: history.map(h => h.value),
                borderColor: 'rgba(132, 204, 22, 1)',
                backgroundColor: 'rgba(132, 204, 22, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    display: true,
                    labels: { color: '#f1f5f9' }
                }
            },
            scales: {
                y: {
                    ticks: { color: '#94a3b8' },
                    grid: { color: '#334155' }
                },
                x: {
                    ticks: { 
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

// ============================================
// Event Listeners
// ============================================
function initEventListeners() {
    // Security dashboard
    document.getElementById('refreshDetections')?.addEventListener('click', loadRecentDetections);
    document.getElementById('zonePeriod')?.addEventListener('change', loadZoneStatistics);
    document.getElementById('recordingSort')?.addEventListener('change', loadRecordings);
    
    // Agriculture dashboard
    document.getElementById('refreshSensors')?.addEventListener('click', loadSensorData);
    document.getElementById('refreshAlerts')?.addEventListener('click', loadAgricultureAlerts);
    document.getElementById('sensorType')?.addEventListener('change', loadSensorHistory);
    document.getElementById('historyPeriod')?.addEventListener('change', loadSensorHistory);
    
    // Irrigation controls
    document.getElementById('startIrrigationBtn')?.addEventListener('click', () => {
        const duration = parseInt(document.getElementById('irrigationDuration').value);
        controlIrrigation('start', duration);
    });
    document.getElementById('stopIrrigationBtn')?.addEventListener('click', () => {
        controlIrrigation('stop');
    });
    document.getElementById('autoModeBtn')?.addEventListener('click', () => {
        controlIrrigation('auto');
    });
}

// ============================================
// System Status
// ============================================
function updateSystemStatus(status) {
    const dot = document.getElementById('systemStatusDot');
    const text = document.getElementById('systemStatusText');
    
    if (status === 'online') {
        dot.style.background = 'var(--success-color)';
        dot.classList.remove('offline');
        text.textContent = 'Online';
    } else if (status === 'offline') {
        dot.style.background = 'var(--danger-color)';
        dot.classList.add('offline');
        text.textContent = 'Offline';
    } else if (status === 'error') {
        dot.style.background = 'var(--warning-color)';
        dot.classList.add('offline');
        text.textContent = 'Connection Error';
    }
}

// ============================================
// Periodic Updates
// ============================================
function updateDashboard() {
    if (currentMode === 'security') {
        loadSecurityStats();
        loadRecentDetections();
    } else {
        loadSensorData();
        loadIrrigationStatus();
    }
}

// ============================================
// Utility Functions
// ============================================
function updateSensorDisplay(sensorData) {
    // Update specific sensor displays based on WebSocket data
    for (const [name, value] of Object.entries(sensorData)) {
        const element = document.getElementById(name);
        if (element) {
            element.textContent = typeof value === 'number' ? value.toFixed(1) : value;
        }
    }
}

// Export functions for inline event handlers
window.playRecording = playRecording;
window.downloadRecording = downloadRecording;

console.log('✅ Dashboard JavaScript loaded');
