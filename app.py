import os
import io
import csv
import time
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from werkzeug.utils import secure_filename
from database import get_db, init_db
from otel_config import setup_otel
from opentelemetry import trace

app = Flask(__name__)
setup_otel(app)
tracer = trace.get_tracer(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads', 'covers')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_cover(file):
    """Save cover file, return filename or None."""
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{int(time.time())}_{secure_filename(file.filename)}"
    if not filename.lower().endswith(('.' + ext)):
        filename = f"{int(time.time())}_cover.{ext}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file.save(os.path.join(UPLOAD_DIR, filename))
    return filename


def delete_cover(filename):
    """Remove a cover file from disk if it exists."""
    if filename:
        path = os.path.join(UPLOAD_DIR, filename)
        try:
            os.remove(path)
        except OSError:
            pass


def book_row_to_dict(row):
    return dict(row)


def build_book_query(q=None, book_type=None, status=None, rating=None,
                     sort='created_at', order='desc', limit=60, offset=0):
    """Build SELECT query for books with optional FTS search and filters."""
    valid_sorts = {'created_at', 'title', 'author', 'year', 'rating', 'pages'}
    if sort not in valid_sorts:
        sort = 'created_at'
    order = 'ASC' if order and order.lower() == 'asc' else 'DESC'

    params = []
    conditions = []

    if q and q.strip():
        # FTS path
        fts_term = q.strip().replace('"', '') + '*'
        base = """
            SELECT books.*
            FROM books
            JOIN books_fts ON books.id = books_fts.rowid
            WHERE books_fts MATCH ?
        """
        params.append(fts_term)

        if book_type:
            conditions.append("books.type = ?")
            params.append(book_type)
        if status:
            conditions.append("books.status = ?")
            params.append(status)
        if rating:
            conditions.append("books.rating = ?")
            params.append(int(rating))

        where_clause = (" AND " + " AND ".join(conditions)) if conditions else ""
        order_clause = f"ORDER BY rank" if not conditions else f"ORDER BY rank"
        sql = base + where_clause + f" {order_clause} LIMIT ? OFFSET ?"
        params += [limit, offset]
    else:
        # Plain SELECT path
        base = "SELECT * FROM books"

        if book_type:
            conditions.append("type = ?")
            params.append(book_type)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if rating:
            conditions.append("rating = ?")
            params.append(int(rating))

        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = base + where_clause + f" ORDER BY {sort} {order} LIMIT ? OFFSET ?"
        params += [limit, offset]

    return sql, params


# ─── Page routes ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html', page='home')


@app.route('/physical')
def physical():
    return render_template('physical.html', page='physical')


@app.route('/ebooks')
def ebooks():
    return render_template('ebooks.html', page='ebooks')


@app.route('/stats')
def stats():
    return render_template('stats.html', page='stats')


# ─── Image serving ──────────────────────────────────────────────────────────

@app.route('/uploads/covers/<path:filename>')
def serve_cover(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ─── API: books ─────────────────────────────────────────────────────────────

@app.route('/api/books', methods=['GET'])
def api_books_list():
    q = request.args.get('q', '').strip()
    book_type = request.args.get('type', '')
    status = request.args.get('status', '')
    rating = request.args.get('rating', '')
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    limit = min(int(request.args.get('limit', 60)), 200)
    offset = int(request.args.get('offset', 0))

    sql, params = build_book_query(
        q=q or None,
        book_type=book_type or None,
        status=status or None,
        rating=rating or None,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset
    )

    db = get_db()
    try:
        rows = db.execute(sql, params).fetchall()
        return jsonify([book_row_to_dict(r) for r in rows])
    finally:
        db.close()


@app.route('/api/books', methods=['POST'])
def api_books_create():
    title = request.form.get('title', '').strip()
    author = request.form.get('author', '').strip()
    if not title or not author:
        return jsonify({'error': 'title and author are required'}), 400

    book_type = request.form.get('type', 'physical')
    if book_type not in ('physical', 'ebook'):
        book_type = 'physical'

    status = request.form.get('status', 'unread')
    if status not in ('unread', 'read', 'abandoned', 'borrowed'):
        status = 'unread'

    genre = request.form.get('genre', '').strip() or None
    publisher = request.form.get('publisher', '').strip() or None
    year_raw = request.form.get('year', '').strip()
    year = int(year_raw) if year_raw.isdigit() else None
    pages_raw = request.form.get('pages', '').strip()
    pages = int(pages_raw) if pages_raw.isdigit() else None
    rating_raw = request.form.get('rating', '').strip()
    rating = int(rating_raw) if rating_raw.isdigit() and 1 <= int(rating_raw) <= 5 else None

    cover_file = request.files.get('cover')
    cover = save_cover(cover_file)

    with tracer.start_as_current_span("books.create") as span:
        span.set_attribute("book.type", book_type)
        span.set_attribute("book.status", status)
        db = get_db()
        try:
            cur = db.execute(
                """INSERT INTO books (title, author, genre, publisher, year, type, pages, cover, rating, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, author, genre, publisher, year, book_type, pages, cover, rating, status)
            )
            db.commit()
            book = db.execute("SELECT * FROM books WHERE id = ?", (cur.lastrowid,)).fetchone()
            return jsonify(book_row_to_dict(book)), 201
        finally:
            db.close()


@app.route('/api/books/<int:book_id>', methods=['GET'])
def api_books_get(book_id):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not row:
            return jsonify({'error': 'not found'}), 404
        return jsonify(book_row_to_dict(row))
    finally:
        db.close()


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def api_books_update(book_id):
    db = get_db()
    try:
        existing = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not existing:
            return jsonify({'error': 'not found'}), 404

        title = request.form.get('title', existing['title']).strip() or existing['title']
        author = request.form.get('author', existing['author']).strip() or existing['author']
        book_type = request.form.get('type', existing['type'])
        if book_type not in ('physical', 'ebook'):
            book_type = existing['type']
        status = request.form.get('status', existing['status'])
        if status not in ('unread', 'read', 'abandoned', 'borrowed'):
            status = existing['status']

        genre = request.form.get('genre', existing['genre'] or '').strip() or None
        publisher = request.form.get('publisher', existing['publisher'] or '').strip() or None
        year_raw = request.form.get('year', str(existing['year'] or '')).strip()
        year = int(year_raw) if year_raw.isdigit() else existing['year']
        pages_raw = request.form.get('pages', str(existing['pages'] or '')).strip()
        pages = int(pages_raw) if pages_raw.isdigit() else existing['pages']
        rating_raw = request.form.get('rating', str(existing['rating'] or '')).strip()
        rating = int(rating_raw) if rating_raw.isdigit() and 1 <= int(rating_raw) <= 5 else existing['rating']

        cover_file = request.files.get('cover')
        if cover_file and cover_file.filename:
            new_cover = save_cover(cover_file)
            if new_cover:
                delete_cover(existing['cover'])
                cover = new_cover
            else:
                cover = existing['cover']
        else:
            cover = existing['cover']

        db.execute(
            """UPDATE books SET title=?, author=?, genre=?, publisher=?, year=?, type=?,
               pages=?, cover=?, rating=?, status=? WHERE id=?""",
            (title, author, genre, publisher, year, book_type, pages, cover, rating, status, book_id)
        )
        db.commit()
        updated = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return jsonify(book_row_to_dict(updated))
    finally:
        db.close()


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def api_books_delete(book_id):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if not row:
            return jsonify({'error': 'not found'}), 404
        delete_cover(row['cover'])
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        db.commit()
        return jsonify({'ok': True})
    finally:
        db.close()


# ─── API: stats ─────────────────────────────────────────────────────────────

@app.route('/api/export/csv')
def export_csv():
    with tracer.start_as_current_span("books.export_csv"):
        db = get_db()
        try:
            rows = db.execute(
                "SELECT id, title, author, genre, publisher, year, type, pages, rating, status, created_at FROM books ORDER BY created_at"
            ).fetchall()
        finally:
            db.close()

        STATUS_PT = {'unread': 'Não lido', 'read': 'Lido', 'abandoned': 'Abandonado', 'borrowed': 'Emprestado'}
        TYPE_PT   = {'physical': 'Físico', 'ebook': 'E-book'}

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['ID', 'Título', 'Autor', 'Gênero', 'Editora', 'Ano', 'Tipo', 'Páginas', 'Nota', 'Estado', 'Cadastrado em'])
        for r in rows:
            writer.writerow([
                r['id'],
                r['title'],
                r['author'],
                r['genre'] or '',
                r['publisher'] or '',
                r['year'] or '',
                TYPE_PT.get(r['type'], r['type']),
                r['pages'] or '',
                r['rating'] or '',
                STATUS_PT.get(r['status'], r['status']),
                r['created_at'],
            ])

        csv_bytes = output.getvalue().encode('utf-8-sig')  # utf-8-sig for Excel compatibility
        return Response(
            csv_bytes,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename="biblioteca.csv"'}
        )


@app.route('/api/stats')
def api_stats():
    with tracer.start_as_current_span("books.stats"):
        db = get_db()
        try:
            by_status = db.execute(
                "SELECT status, COUNT(*) as count FROM books GROUP BY status ORDER BY count DESC"
            ).fetchall()
            by_rating = db.execute(
                "SELECT rating, COUNT(*) as count FROM books GROUP BY rating ORDER BY rating"
            ).fetchall()
            total = db.execute("SELECT COUNT(*) as count FROM books").fetchone()['count']
            by_type = db.execute(
                "SELECT type, COUNT(*) as count FROM books GROUP BY type"
            ).fetchall()
            return jsonify({
                'total': total,
                'by_status': [dict(r) for r in by_status],
                'by_rating': [dict(r) for r in by_rating],
                'by_type': [dict(r) for r in by_type],
            })
        finally:
            db.close()


if __name__ == '__main__':
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    init_db()
    app.run(debug=True, port=5003)
