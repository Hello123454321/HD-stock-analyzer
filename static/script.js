const API = 'http://localhost:5000/api';

async function analyzeStock() {
    const symbol = document.getElementById('symbolInput').value.trim().toUpperCase();
    if (!symbol) return alert('Please enter a stock symbol');

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');

    try {
        const res = await fetch(`${API}/analyze/${symbol}`);
        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        renderMetrics(data.data);
        renderAnalysis(data.analysis, symbol);

        document.getElementById('results').classList.remove('hidden');
    } catch (err) {
        alert('Error connecting to server. Make sure Flask is running.');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

function renderMetrics(d) {
    const fmt = (n) => n ? '$' + Number(n).toLocaleString() : 'N/A';
    const pct = (n) => n ? n.toFixed(1) + '%' : 'N/A';

    const metrics = [
        { label: 'Stock Price', value: d.price ? `$${d.price}` : 'N/A' },
        { label: 'Daily Volume', value: d.volume ? Number(d.volume).toLocaleString() : 'N/A' },
        { label: 'Revenue', value: fmt(d.revenue) },
        { label: 'COGs', value: fmt(d.cogs) },
        { label: 'SG&A', value: fmt(d.sgna) },
        { label: 'Interest Expense', value: fmt(d.interest_expense) },
        { label: 'Net Profit', value: fmt(d.net_profit) },
        { label: 'Gross Margin', value: pct(d.gross_margin) },
        { label: 'Net Margin', value: pct(d.net_margin) },
    ];

    document.getElementById('metricsGrid').innerHTML = metrics.map(m => `
        <div class="metric-card">
            <div class="label">${m.label}</div>
            <div class="value">${m.value}</div>
        </div>
    `).join('');
}

function renderAnalysis(text, symbol) {
    document.getElementById('analysisBox').innerHTML = `
        <h3 style="color:#6c8fff; margin-bottom:16px;">🤖 AI Analysis: ${symbol}</h3>
        <div>${text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</div>
    `;
}

async function loadTopPicks() {
    const res = await fetch(`${API}/top-picks`);
    const picks = await res.json();

    document.getElementById('topPicksList').innerHTML = picks.map(p => `
        <div class="pick-card" onclick="quickAnalyze('${p.symbol}')">
            <span class="symbol">${p.symbol}</span>
            <span>Price: $${p.price || 'N/A'}</span>
            <span class="margin">Net Margin: ${p.net_margin ? p.net_margin.toFixed(1) + '%' : 'N/A'}</span>
        </div>
    `).join('');
}

function quickAnalyze(symbol) {
    document.getElementById('symbolInput').value = symbol;
    analyzeStock();
}

// Allow Enter key to trigger search
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('symbolInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') analyzeStock();
    });
});