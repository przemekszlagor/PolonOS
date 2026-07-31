let chartInstance = null;

// File size formatting helper
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0.00 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Network speed formatting helper
function formatSpeed(bytesPerSec) {
    const bitsPerSec = bytesPerSec * 8;
    if (bitsPerSec >= 1000000) {
        return { val: (bitsPerSec / 1000000).toFixed(1), unit: 'Mb/s', mbps: bitsPerSec / 1000000 };
    } else if (bitsPerSec >= 1000) {
        return { val: (bitsPerSec / 1000).toFixed(0), unit: 'Kb/s', mbps: bitsPerSec / 1000000 };
    } else {
        return { val: bitsPerSec.toFixed(0), unit: 'b/s', mbps: bitsPerSec / 1000000 };
    }
}

// Dynamic scaling of SVG rings
function setRingProgress(elementId, value, maxVal) {
    const ring = document.getElementById(elementId);
    if (!ring) return;
    
    const totalLength = parseFloat(ring.getAttribute('stroke-dasharray'));
    const percent = Math.min(1.0, value / maxVal);
    const offset = totalLength - (totalLength * percent);
    ring.style.strokeDashoffset = offset;
}

// Custom Premium Canvas Chart with PolonOS styling
class RealtimeChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.maxPoints = 60;
        this.downData = new Array(this.maxPoints).fill(0);
        this.upData = new Array(this.maxPoints).fill(0);
        
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.width = rect.width;
        this.height = rect.height;
        this.draw();
    }
    
    addData(down, up) {
        this.downData.push(down);
        this.downData.shift();
        this.upData.push(up);
        this.upData.shift();
        this.draw();
    }
    
    draw() {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        if (!ctx || !w || !h) return;
        
        ctx.clearRect(0, 0, w, h);
        
        let maxVal = Math.max(...this.downData, ...this.upData, 2.0); // minimum scale 2 Mbps
        maxVal = Math.ceil(maxVal / 5) * 5; // round to nearest 5
        
        // Draw grid
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
        ctx.lineWidth = 1;
        const gridLines = 4;
        for (let i = 0; i <= gridLines; i++) {
            const y = (h - 20) * (1 - i / gridLines) + 10;
            ctx.beginPath();
            ctx.moveTo(40, y);
            ctx.lineTo(w, y);
            ctx.stroke();
            
            // Draw labels
            ctx.fillStyle = '#5e646d';
            ctx.font = '10px Outfit';
            ctx.fillText(((maxVal / gridLines) * i).toFixed(1) + ' M', 5, y + 4);
        }
        
        // Plot curves (Down = Red Carbon, Up = Silver)
        this.drawLine(this.downData, '#c22e45', 'rgba(194, 46, 69, 0.06)', maxVal);
        this.drawLine(this.upData, '#d8dce2', 'rgba(216, 220, 226, 0.05)', maxVal);
    }
    
    drawLine(data, strokeColor, fillColor, maxVal) {
        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const padX = 40;
        const graphW = w - padX;
        const graphH = h - 20;
        const stepX = graphW / (this.maxPoints - 1);
        
        ctx.beginPath();
        for (let i = 0; i < data.length; i++) {
            const val = data[i];
            const x = padX + i * stepX;
            const y = graphH * (1 - val / maxVal) + 10;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                const prevX = padX + (i - 1) * stepX;
                const prevY = graphH * (1 - data[i - 1] / maxVal) + 10;
                const cpX1 = prevX + stepX / 2;
                const cpY1 = prevY;
                const cpX2 = prevX + stepX / 2;
                const cpY2 = y;
                ctx.bezierCurveTo(cpX1, cpY1, cpX2, cpY2, x, y);
            }
        }
        
        ctx.save();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2.2;
        ctx.shadowColor = strokeColor;
        ctx.shadowBlur = 6;
        ctx.stroke();
        ctx.restore();
        
        ctx.lineTo(w, graphH + 10);
        ctx.lineTo(padX, graphH + 10);
        ctx.closePath();
        
        const grad = ctx.createLinearGradient(0, 10, 0, graphH + 10);
        grad.addColorStop(0, fillColor);
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = grad;
        ctx.fill();
    }
}

// Communications
function postToPython(message) {
    try {
        if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.app) {
            window.webkit.messageHandlers.app.postMessage(JSON.stringify(message));
        } else if (window.webkit && window.webkit.message_handlers && window.webkit.message_handlers.app) {
            window.webkit.message_handlers.app.postMessage(JSON.stringify(message));
        } else {
            console.error('No python message handler found');
        }
    } catch (e) {
        console.error('Failed to post message to Python:', e);
    }
}

// Listen to Python events
window.addEventListener('polonosnetmonitor-event', (e) => {
    try {
        const eventData = JSON.parse(e.detail);
        const type = eventData.type;
        const payload = eventData.payload;
        
        switch (type) {
            case 'realtime-stats':
                handleRealtimeStats(payload);
                break;
            case 'ip-details':
                handleIpDetails(payload);
                break;
            case 'speedtest-update':
                handleSpeedtestUpdate(payload);
                break;
        }
    } catch (err) {
        console.error('Error handling python event:', err);
    }
});

// Event Handler: Realtime Stats
function handleRealtimeStats(stats) {
    const statusPill = document.getElementById('connection-status-pill');
    const statusText = document.getElementById('connection-status-text');
    
    if (stats.connected) {
        statusPill.className = 'connection-pill online';
        statusText.innerText = 'Połączono';
    } else {
        statusPill.className = 'connection-pill offline';
        statusText.innerText = 'Brak sieci';
    }
    
    document.getElementById('net-interface').innerText = stats.interface;
    document.getElementById('net-local-ip').innerText = stats.local_ip;
    
    const typeLabel = document.getElementById('net-type');
    if (stats.connected) {
        if (stats.connection_type === 'wifi') {
            typeLabel.innerText = `Wi-Fi (${stats.wifi_ssid}) - ${stats.wifi_signal}%`;
        } else if (stats.connection_type === 'ethernet') {
            typeLabel.innerText = 'Ethernet (Kablowe)';
        } else {
            typeLabel.innerText = 'Połączono';
        }
    } else {
        typeLabel.innerText = 'Brak sieci';
        document.getElementById('net-local-ip').innerText = '-';
    }
    
    const down = formatSpeed(stats.down_speed);
    const up = formatSpeed(stats.up_speed);
    
    document.getElementById('realtime-down-val').innerText = down.val;
    document.getElementById('realtime-down-unit').innerText = down.unit;
    document.getElementById('realtime-up-val').innerText = up.val;
    document.getElementById('realtime-up-unit').innerText = up.unit;
    
    // Scale rings: max 100 Mbps, but dynamic cap is clean
    setRingProgress('gauge-down-ring', down.mbps, 100);
    setRingProgress('gauge-up-ring', up.mbps, 100);
    
    document.getElementById('session-rx').innerText = formatBytes(stats.total_rx);
    document.getElementById('session-tx').innerText = formatBytes(stats.total_tx);
    
    if (chartInstance) {
        chartInstance.addData(down.mbps, up.mbps);
    }
}

// Event Handler: IP & ISP Details
function handleIpDetails(details) {
    document.getElementById('net-ip').innerText = details.ip;
}

// App Initialization
document.addEventListener('DOMContentLoaded', () => {
    chartInstance = new RealtimeChart('realtime-chart');
    
    setTimeout(() => {
        if (chartInstance) chartInstance.resize();
    }, 150);
    
    setTimeout(() => {
        const hasHandlers = (window.webkit && (window.webkit.messageHandlers || window.webkit.message_handlers));
        document.title = hasHandlers ? "webkit-ok" : "webkit-undefined";
        postToPython({ action: 'get-ip-details' });
    }, 500);
});

// Speedtest logic
function startSpeedtest() {
    const btn = document.getElementById('speedtest-btn');
    const body = document.getElementById('speedtest-body');
    const progress = document.getElementById('speedtest-progress-bar');
    const downVal = document.getElementById('speedtest-down');
    const upVal = document.getElementById('speedtest-up');

    btn.disabled = true;
    btn.innerText = 'Testuję...';
    body.style.display = 'flex';
    progress.style.width = '0%';
    downVal.innerText = '- Mb/s';
    upVal.innerText = '- Mb/s';

    postToPython({ action: 'run-speedtest' });
}

function handleSpeedtestUpdate(payload) {
    const btn = document.getElementById('speedtest-btn');
    const progress = document.getElementById('speedtest-progress-bar');
    const downVal = document.getElementById('speedtest-down');
    const upVal = document.getElementById('speedtest-up');

    progress.style.width = payload.progress + '%';

    if (payload.status === 'downloading') {
        downVal.innerText = payload.speed.toFixed(1) + ' Mb/s';
    } else if (payload.status === 'uploading') {
        upVal.innerText = payload.speed.toFixed(1) + ' Mb/s';
    } else if (payload.status === 'complete') {
        downVal.innerText = payload.speed.download.toFixed(1) + ' Mb/s';
        upVal.innerText = payload.speed.upload.toFixed(1) + ' Mb/s';
        btn.disabled = false;
        btn.innerText = 'Uruchom Speedtest';
    }
}
