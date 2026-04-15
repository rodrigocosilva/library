// Book card rendering and page logic

const STATUS_LABEL = {
  unread: 'Não lido',
  read: 'Lido',
  abandoned: 'Abandonado',
  borrowed: 'Emprestado',
};

const STATUS_CLASS = {
  unread: 'badge--unread',
  read: 'badge--read',
  abandoned: 'badge--abandoned',
  borrowed: 'badge--borrowed',
};

function starsHTML(rating) {
  if (!rating) return '<span class="no-rating">Sem nota</span>';
  let s = '';
  for (let i = 1; i <= 5; i++) {
    s += `<span class="star ${i <= rating ? 'star--on' : 'star--off'}">★</span>`;
  }
  return s;
}

function bookCard(book) {
  const cover = book.cover
    ? `/uploads/covers/${encodeURIComponent(book.cover)}`
    : '/static/img/placeholder.svg';

  return `
    <div class="book-card" data-id="${book.id}">
      <div class="book-cover-wrap" onclick="openModal(${book.id})">
        <img class="book-cover" src="${cover}" alt="${escHtml(book.title)}"
             onerror="this.src='/static/img/placeholder.svg'" loading="lazy" />
        <div class="book-cover-overlay">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </div>
      </div>
      <div class="book-info">
        <div class="book-title" title="${escHtml(book.title)}">${escHtml(book.title)}</div>
        <div class="book-author">${escHtml(book.author)}</div>
        <div class="book-meta-row">
          <span class="badge ${STATUS_CLASS[book.status] || ''}">${STATUS_LABEL[book.status] || book.status}</span>
          <span class="book-type-tag">${book.type === 'ebook' ? 'E-book' : 'Físico'}</span>
        </div>
        <div class="book-stars">${starsHTML(book.rating)}</div>
      </div>
      <button class="book-delete-btn" onclick="deleteBook(event, ${book.id})" title="Excluir">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
      </button>
    </div>
  `;
}

function escHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Page state ───────────────────────────────────────────────────────────────

let _pageType = null;
let _offset = 0;
const _limit = 60;
let _loading = false;
let _allLoaded = false;

function getFilters() {
  const status = document.getElementById('filter-status')?.value || '';
  const sort = document.getElementById('filter-sort')?.value || 'created_at';
  const q = new URLSearchParams(window.location.search).get('q') || '';
  return { status, sort, q };
}

function buildParams(extra = {}) {
  const { status, sort, q } = getFilters();
  const p = new URLSearchParams();
  if (q) p.set('q', q);
  if (_pageType) p.set('type', _pageType);
  if (status) p.set('status', status);
  p.set('sort', sort);
  p.set('order', sort === 'title' || sort === 'author' ? 'asc' : 'desc');
  p.set('limit', _limit);
  p.set('offset', extra.offset ?? 0);
  return p;
}

async function fetchBooks(offset = 0) {
  const params = buildParams({ offset });
  const res = await fetch(`/api/books?${params}`);
  return res.json();
}

function renderGrid(books, append = false) {
  const grid = document.getElementById('books-grid');
  if (!append) grid.innerHTML = '';

  if (!books.length && !append) {
    grid.innerHTML = `<div class="empty-state"><p>Nenhum livro encontrado.</p><button class="btn-primary" onclick="openModal()">Adicionar primeiro livro</button></div>`;
    return;
  }

  books.forEach(b => {
    const div = document.createElement('div');
    div.innerHTML = bookCard(b);
    grid.appendChild(div.firstElementChild);
  });
}

function updateCount(books, append) {
  const el = document.getElementById('books-count');
  if (!el) return;
  if (!append && books.length === 0) {
    el.textContent = 'Nenhum livro encontrado';
  } else if (!append) {
    el.textContent = books.length < _limit
      ? `${books.length} livro${books.length !== 1 ? 's' : ''}`
      : `${books.length}+ livros`;
  }
}

async function loadBooks() {
  if (_loading) return;
  _loading = true;
  _offset = 0;
  _allLoaded = false;

  const grid = document.getElementById('books-grid');
  grid.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Carregando livros…</p></div>`;

  try {
    const books = await fetchBooks(0);
    _offset = books.length;
    _allLoaded = books.length < _limit;
    renderGrid(books);
    updateCount(books, false);

    const moreWrap = document.getElementById('load-more-wrap');
    if (moreWrap) moreWrap.classList.toggle('hidden', _allLoaded);
  } finally {
    _loading = false;
  }
}

async function loadMore() {
  if (_loading || _allLoaded) return;
  _loading = true;
  try {
    const books = await fetchBooks(_offset);
    _offset += books.length;
    _allLoaded = books.length < _limit;
    renderGrid(books, true);

    const moreWrap = document.getElementById('load-more-wrap');
    if (moreWrap) moreWrap.classList.toggle('hidden', _allLoaded);
  } finally {
    _loading = false;
  }
}

function applyFilters() {
  loadBooks();
}

async function deleteBook(event, id) {
  event.stopPropagation();
  if (!confirm('Excluir este livro?')) return;
  await fetch(`/api/books/${id}`, { method: 'DELETE' });
  const card = document.querySelector(`.book-card[data-id="${id}"]`);
  if (card) card.remove();
}

function initBooksPage(opts = {}) {
  _pageType = opts.type || null;
  loadBooks();
}

// Expose for modal.js to call after save
window._reloadBooks = loadBooks;
