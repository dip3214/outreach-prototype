"""
Postgres storage layer (Supabase). Everything the app knows lives in
one Postgres database instead of a local SQLite file, so nothing is
lost on redeploy or restart.

Set DATABASE_URL to your Supabase connection string, e.g.:
    postgresql://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres

Find it in Supabase: Project Settings -> Database -> Connection string.
If deploying somewhere serverless/short-lived (Streamlit Cloud, Vercel,
Netlify functions, etc.), use the "Connection pooling" string instead
(port 6543) -- it handles many short connections better than the
direct one.
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add your Supabase connection string "
            "as an environment variable (or Streamlit secret) named DATABASE_URL."
        )
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            company TEXT,
            sector TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER NOT NULL REFERENCES contacts (id),
            event_type TEXT NOT NULL,
            detail TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def upsert_contacts(rows):
    """rows: list of dicts with keys name, email, company, sector (sector may be None)."""
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    inserted, skipped = 0, 0
    for r in rows:
        email = (r.get("email") or "").strip().lower()
        if not email or "@" not in email:
            skipped += 1
            continue
        cur.execute(
            "INSERT INTO contacts (name, email, company, sector, status, created_at) "
            "VALUES (%s, %s, %s, %s, 'pending', %s) "
            "ON CONFLICT (email) DO NOTHING",
            (r.get("name", "").strip(), email, r.get("company", "").strip(),
             r.get("sector") or None, now),
        )
        if cur.rowcount == 1:
            inserted += 1
        else:
            skipped += 1  # duplicate email, already in the list
    conn.commit()
    cur.close()
    conn.close()
    return inserted, skipped


def log_event(contact_id, event_type, detail=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (contact_id, event_type, detail, timestamp) VALUES (%s, %s, %s, %s)",
        (contact_id, event_type, detail, datetime.now(timezone.utc).isoformat()),
    )
    cur.execute("UPDATE contacts SET status = %s WHERE id = %s", (event_type, contact_id))
    conn.commit()
    cur.close()
    conn.close()


def get_contacts(status=None):
    conn = get_conn()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM contacts WHERE status = %s", (status,))
    else:
        cur.execute("SELECT * FROM contacts")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_metrics():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM contacts")
    total_contacts = cur.fetchone()["c"]

    counts = {}
    cur.execute("SELECT event_type, COUNT(*) c FROM events GROUP BY event_type")
    for row in cur.fetchall():
        counts[row["event_type"]] = row["c"]

    cur.execute("""
        SELECT date(timestamp::timestamptz) d, event_type, COUNT(*) c
        FROM events GROUP BY d, event_type ORDER BY d
    """)
    daily = cur.fetchall()

    cur.close()
    conn.close()
    return {
        "total_contacts": total_contacts,
        "sent": counts.get("sent", 0),
        "bounced": counts.get("bounced", 0),
        "replied": counts.get("replied", 0),
        "daily": [dict(r) for r in daily],
    }
