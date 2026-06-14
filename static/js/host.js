// host.js - Host dashboard and live panel controls

function updateLeaderboard(sessionId) {
    fetch(`/api/leaderboard/${sessionId}`, { cache: 'no-store' })
        .then(res => res.json())
        .then(data => {
            if (data.leaderboard) {
                const tbody = document.getElementById('leaderboard-body');
                if (tbody) {
                    tbody.innerHTML = '';
                    data.leaderboard.forEach(row => {
                        const tr = document.createElement('tr');
                        tr.className = 'leaderboard-row';
                        tr.innerHTML = `
                            <td>${row.rank}</td>
                            <td>${row.fullname}</td>
                            <td>${row.score}</td>
                            <td>${row.accuracy.toFixed(1)}%</td>
                            <td>${row.average_response_time.toFixed(1)}s</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            }
        });
}

function pollSessionStatus(sessionId) {
    setInterval(() => {
        fetch(`/api/get_session_status/${sessionId}`, { cache: 'no-store' })
            .then(res => res.json())
            .then(data => {
                const countEl = document.getElementById('participant-count');
                if (countEl && data.participant_count !== undefined) {
                    countEl.textContent = data.participant_count;
                }
                
                // Update leaderboard every tick
                updateLeaderboard(sessionId);
            });
    }, 2000);
}

function controlQuiz(action, sessionId) {
    fetch(`/api/${action}/${sessionId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Refresh or handle UI
                window.location.reload();
            } else {
                alert(data.error || 'Action failed');
            }
        });
}
