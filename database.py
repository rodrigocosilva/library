import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'library.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            author      TEXT    NOT NULL,
            genre       TEXT,
            publisher   TEXT,
            year        INTEGER,
            type        TEXT    NOT NULL CHECK(type IN ('physical', 'ebook')),
            pages       INTEGER,
            cover       TEXT,
            rating      INTEGER CHECK(rating BETWEEN 1 AND 5),
            status      TEXT    NOT NULL DEFAULT 'unread'
                                CHECK(status IN ('unread', 'read', 'abandoned', 'borrowed')),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_books_type   ON books(type);
        CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
        CREATE INDEX IF NOT EXISTS idx_books_rating ON books(rating);

        CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
            title,
            author,
            publisher,
            content='books',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON books BEGIN
            INSERT INTO books_fts(rowid, title, author, publisher)
            VALUES (new.id, new.title, new.author, COALESCE(new.publisher, ''));
        END;

        CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, title, author, publisher)
            VALUES ('delete', old.id, old.title, old.author, COALESCE(old.publisher, ''));
        END;

        CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, title, author, publisher)
            VALUES ('delete', old.id, old.title, old.author, COALESCE(old.publisher, ''));
            INSERT INTO books_fts(rowid, title, author, publisher)
            VALUES (new.id, new.title, new.author, COALESCE(new.publisher, ''));
        END;
    """)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("Database initialized at", DB_PATH)
