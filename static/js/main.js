// ── Theme toggle ────────────────────────────────────────────────────────────

function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  const moon = document.getElementById('icon-moon');
  const sun  = document.getElementById('icon-sun');
  if (moon) moon.style.display = dark ? 'none' : '';
  if (sun)  sun.style.display  = dark ? '' : 'none';
}

function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const next = !isDark;
  localStorage.setItem('theme', next ? 'dark' : 'light');
  applyTheme(next);
}

// Apply saved theme immediately (before DOMContentLoaded to avoid flash)
(function () {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved === 'dark' || (!saved && prefersDark));
})();

// ── Search bar — debounce + URL redirect ────────────────────────────────────

(function () {
  const input = document.getElementById('searchInput');
  if (!input) return;

  // Pre-fill from URL
  const params = new URLSearchParams(window.location.search);
  if (params.get('q')) input.value = params.get('q');

  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = input.value.trim();
      const url = new URL(window.location.href);
      if (q) {
        url.searchParams.set('q', q);
      } else {
        url.searchParams.delete('q');
      }
      window.location.href = url.toString();
    }, 350);
  });
})();
