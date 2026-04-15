// Statistics page — Chart.js charts

const COLORS_STATUS = {
  read:      '#4ade80',
  unread:    '#94a3b8',
  abandoned: '#f87171',
  borrowed:  '#fbbf24',
};

const COLORS_RATING = ['#ef4444','#f97316','#eab308','#22c55e','#3b82f6','#6b7280'];

const STATUS_LABEL = {
  read: 'Lido', unread: 'Não lido', abandoned: 'Abandonado', borrowed: 'Emprestado',
};

function buildLegend(containerId, labels, colors, counts) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = labels.map((l, i) => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${colors[i]}"></span>
      <span class="legend-label">${l}</span>
      <span class="legend-count">${counts[i]}</span>
    </div>
  `).join('');
}

async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();

  const totalEl = document.getElementById('stats-total');
  if (totalEl) totalEl.textContent = `${data.total} livro${data.total !== 1 ? 's' : ''} cadastrado${data.total !== 1 ? 's' : ''}`;

  // Stat cards
  const cards = document.getElementById('stat-cards');
  if (cards) {
    const physCount = (data.by_type.find(t => t.type === 'physical') || {}).count || 0;
    const ebCount   = (data.by_type.find(t => t.type === 'ebook')    || {}).count || 0;
    const readCount = (data.by_status.find(s => s.status === 'read') || {}).count || 0;
    const avgRating = (() => {
      let sum = 0, cnt = 0;
      data.by_rating.forEach(r => { if (r.rating) { sum += r.rating * r.count; cnt += r.count; } });
      return cnt ? (sum / cnt).toFixed(1) : '-';
    })();

    cards.innerHTML = `
      <div class="stat-card"><div class="stat-value">${data.total}</div><div class="stat-label">Total</div></div>
      <div class="stat-card"><div class="stat-value">${physCount}</div><div class="stat-label">Físicos</div></div>
      <div class="stat-card"><div class="stat-value">${ebCount}</div><div class="stat-label">E-books</div></div>
      <div class="stat-card"><div class="stat-value">${readCount}</div><div class="stat-label">Lidos</div></div>
      <div class="stat-card"><div class="stat-value">${avgRating} ★</div><div class="stat-label">Nota média</div></div>
    `;
  }

  // Chart defaults
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";

  const doughnutOpts = {
    type: 'doughnut',
    options: {
      cutout: '65%',
      plugins: { legend: { display: false }, tooltip: { callbacks: {
        label: ctx => ` ${ctx.label}: ${ctx.parsed} livro${ctx.parsed !== 1 ? 's' : ''}`
      }}},
      animation: { animateScale: true },
    },
  };

  // Status chart
  const statusLabels = data.by_status.map(s => STATUS_LABEL[s.status] || s.status);
  const statusCounts = data.by_status.map(s => s.count);
  const statusColors = data.by_status.map(s => COLORS_STATUS[s.status] || '#6b7280');

  new Chart(document.getElementById('chart-status'), {
    ...doughnutOpts,
    data: { labels: statusLabels, datasets: [{ data: statusCounts, backgroundColor: statusColors, borderWidth: 0, hoverOffset: 6 }] },
  });
  buildLegend('legend-status', statusLabels, statusColors, statusCounts);

  // Rating chart
  const ratingRows = [...data.by_rating].sort((a, b) => (a.rating || 0) - (b.rating || 0));
  const ratingLabels = ratingRows.map(r => r.rating ? `${r.rating} ★` : 'Sem nota');
  const ratingCounts = ratingRows.map(r => r.count);
  const ratingColors = ratingRows.map((_, i) => COLORS_RATING[i] || '#6b7280');

  new Chart(document.getElementById('chart-rating'), {
    ...doughnutOpts,
    data: { labels: ratingLabels, datasets: [{ data: ratingCounts, backgroundColor: ratingColors, borderWidth: 0, hoverOffset: 6 }] },
  });
  buildLegend('legend-rating', ratingLabels, ratingColors, ratingCounts);

  // Type chart
  const typeLabels = data.by_type.map(t => t.type === 'ebook' ? 'E-book' : 'Físico');
  const typeCounts = data.by_type.map(t => t.count);
  const typeColors = ['#6366f1', '#06b6d4'];

  new Chart(document.getElementById('chart-type'), {
    ...doughnutOpts,
    data: { labels: typeLabels, datasets: [{ data: typeCounts, backgroundColor: typeColors, borderWidth: 0, hoverOffset: 6 }] },
  });
  buildLegend('legend-type', typeLabels, typeColors, typeCounts);
}

document.addEventListener('DOMContentLoaded', loadStats);
