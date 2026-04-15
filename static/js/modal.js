// Add / Edit book modal

let _currentRating = 0;

function openModal(bookId) {
  resetForm();
  if (bookId) {
    document.getElementById('modal-title').textContent = 'Editar Livro';
    document.getElementById('btn-submit').textContent = 'Salvar alterações';
    loadBookIntoForm(bookId);
  } else {
    document.getElementById('modal-title').textContent = 'Novo Livro';
    document.getElementById('btn-submit').textContent = 'Adicionar';
  }
  document.getElementById('modal-overlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
  document.body.style.overflow = '';
}

function closeModalOnOverlay(event) {
  if (event.target === document.getElementById('modal-overlay')) closeModal();
}

function resetForm() {
  document.getElementById('book-form').reset();
  document.getElementById('book-id').value = '';
  document.getElementById('cover-preview').src = '/static/img/placeholder.svg';
  setRating(0);
}

async function loadBookIntoForm(id) {
  const res = await fetch(`/api/books/${id}`);
  if (!res.ok) return;
  const b = await res.json();

  document.getElementById('book-id').value = b.id;
  document.getElementById('f-title').value = b.title || '';
  document.getElementById('f-author').value = b.author || '';
  document.getElementById('f-genre').value = b.genre || '';
  document.getElementById('f-publisher').value = b.publisher || '';
  document.getElementById('f-year').value = b.year || '';
  document.getElementById('f-pages').value = b.pages || '';
  document.getElementById('f-type').value = b.type || 'physical';
  document.getElementById('f-status').value = b.status || 'unread';
  setRating(b.rating || 0);

  if (b.cover) {
    document.getElementById('cover-preview').src = `/uploads/covers/${encodeURIComponent(b.cover)}`;
  }
}

function previewCover(event) {
  const file = event.target.files[0];
  if (!file) return;
  const url = URL.createObjectURL(file);
  document.getElementById('cover-preview').src = url;
}

// Star picker
function setRating(val) {
  _currentRating = val;
  document.getElementById('f-rating').value = val || '';
  const btns = document.querySelectorAll('#star-picker button');
  btns.forEach((btn, i) => {
    btn.classList.toggle('star-on', i < val);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('#star-picker button').forEach(btn => {
    btn.addEventListener('click', () => {
      const val = parseInt(btn.dataset.val);
      setRating(_currentRating === val ? 0 : val);
    });
    btn.addEventListener('mouseenter', () => {
      const val = parseInt(btn.dataset.val);
      document.querySelectorAll('#star-picker button').forEach((b, i) => {
        b.classList.toggle('star-hover', i < val);
      });
    });
    btn.addEventListener('mouseleave', () => {
      document.querySelectorAll('#star-picker button').forEach(b => b.classList.remove('star-hover'));
    });
  });
});

async function submitBook(event) {
  event.preventDefault();
  const form = document.getElementById('book-form');
  const id = document.getElementById('book-id').value;
  const formData = new FormData(form);

  const method = id ? 'PUT' : 'POST';
  const url = id ? `/api/books/${id}` : '/api/books';

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.textContent = 'Salvando…';

  try {
    const res = await fetch(url, { method, body: formData });
    if (!res.ok) {
      const err = await res.json();
      alert(err.error || 'Erro ao salvar livro.');
      return;
    }
    closeModal();
    if (typeof window._reloadBooks === 'function') window._reloadBooks();
  } catch (e) {
    alert('Erro de rede. Tente novamente.');
  } finally {
    btn.disabled = false;
  }
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});
