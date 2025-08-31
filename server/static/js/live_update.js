async function fetchLogs() {
    try {
        const response = await fetch('/logs', { credentials: 'include' });
        if (!response.ok) {
            console.error('Failed to fetch logs');
            return;
        }
        const logs = await response.json();
        const tbody = document.getElementById('log-table-body');
        tbody.innerHTML = '';

        logs.slice().reverse().forEach(entry => {
            const tr = document.createElement('tr');
            const timestamp = new Date(entry.timestamp * 1000).toLocaleString();
            tr.innerHTML = `
                <td>${timestamp}</td>
                <td>${entry.count}</td>
                <td><img src="/uploads/${entry.image}" alt="captured image" /></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

// Refresh logs every 5 seconds
setInterval(fetchLogs, 5000);
window.onload = fetchLogs;

