let updateInterval;

function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            // System Status
            const systemStatus = document.getElementById('systemStatus');
            const status = data.system_status;
            systemStatus.innerHTML = `
                <div class="status-indicator">
                    <div class="status-dot status-${status.status}"></div>
                    <span>${status.message}</span>
                </div>
            `;
            
            // Grid Power
            const gridPower = document.getElementById('gridPower');
            const grid = data.grid_power || 0;
            gridPower.innerHTML = `${grid.toFixed(0)}<span class="unit">W</span>`;
            
            // Battery Power
            const batteryPower = document.getElementById('batteryPower');
            const battery = data.battery_power || 0;
            batteryPower.innerHTML = `${battery.toFixed(0)}<span class="unit">W</span>`;
            
            // Batteries
            const batteryGrid = document.getElementById('batteryGrid');
            batteryGrid.innerHTML = '';
            
            Object.entries(data.batteries || {}).forEach(([id, battery]) => {
                const batteryCard = document.createElement('div');
                batteryCard.className = 'battery-card';
                
                const statusClass = battery.error_count > 0 ? 'error' : 'ok';
                
                batteryCard.innerHTML = `
                    <div class="battery-header">
                        <div class="battery-name">Akku ${id}</div>
                        <div class="battery-soc">${battery.soc || 0}%</div>
                    </div>
                    <div class="battery-power">${(battery.power || 0).toFixed(0)}W</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.25rem;">
                        <div class="status-dot status-${statusClass}"></div>
                        ${battery.error_count > 0 ? `Fehler: ${battery.error_count}` : 'Online'}
                    </div>
                `;
                
                batteryGrid.appendChild(batteryCard);
            });
        })
        .catch(error => console.error('Status update error:', error));
}

function updateLogs() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('logContainer');
            const logCount = document.getElementById('logCount');
            
            container.innerHTML = '';
            logCount.textContent = data.logs.length;
            
            data.logs.slice(-20).forEach(log => { // Nur die letzten 20 Logs anzeigen
                const div = document.createElement('div');
                div.className = 'log-entry';
                div.innerHTML = `
                    <span class="log-time">${log.timestamp}</span>
                    <span class="log-level log-${log.level.toLowerCase()}">${log.level}</span>
                    <span class="log-message">${log.message}</span>
                `;
                container.appendChild(div);
            });
            
            container.scrollTop = container.scrollHeight;
        })
        .catch(error => console.error('Log update error:', error));
}

// Initialisierung
window.addEventListener('load', () => {
    updateStatus();
    updateLogs();
    updateInterval = setInterval(() => {
        updateStatus();
        updateLogs();
    }, 2000);
});

// Cleanup on page exit
window.addEventListener('beforeunload', () => {
    if (updateInterval) clearInterval(updateInterval);
});
