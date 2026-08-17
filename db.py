"""Postgres storage layer for the Outreach prototype."""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add your Supabase connection string as "
            "an environment variable (or Streamlit secret) named DATABASE_URL."
        )
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


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
            subject TEXT,
            timestamp TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_emails (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER NOT NULL REFERENCES contacts (id),
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            scheduled_for TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS subject TEXT")
    conn.commit()
    cur.close()
    conn.close()


def upsert_contacts(rows):
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
            "VALUES (%s, %s, %s, %s, 'pending', %s) ON CONFLICT (email) DO NOTHING",
            (str(r.get("name", "")).strip(), email, str(r.get("company", "")).strip(),
             r.get("sector") or None, now),
        )
        if cur.rowcount == 1:
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    cur.close()
    conn.close()
    return inserted, skipped


def log_event(contact_id, event_type, detail="", subject=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (contact_id, event_type, detail, subject, timestamp) VALUES (%s, %s, %s, %s, %s)",
        (contact_id, event_type, detail, subject, datetime.now(timezone.utc).isoformat()),
    )
    cur.execute("UPDATE contacts SET status = %s WHERE id = %s", (event_type, contact_id))
    conn.commit()
    cur.close()
    conn.close()


def get_contacts(status=None):
    conn = get_conn()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM contacts WHERE status = %s ORDER BY created_at DESC", (status,))
    else:
        cur.execute("SELECT * FROM contacts ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_customer_history(contact_id=None):
    conn = get_conn()
    cur = conn.cursor()
    query = """
        SELECT c.id AS customer_id, c.name, c.email, c.company, c.sector,
               e.event_type, e.subject, e.detail, e.timestamp
        FROM contacts c
        LEFT JOIN events e ON e.contact_id = c.id
    """
    params = ()
    if contact_id is not None:
        query += " WHERE c.id = %s"
        params = (contact_id,)
    query += " ORDER BY e.timestamp DESC NULLS LAST, c.name ASC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def schedule_email(contact_id, subject, body, scheduled_for):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO scheduled_emails (contact_id, subject, body, scheduled_for, status, created_at) "
        "VALUES (%s, %s, %s, %s, 'scheduled', %s)",
        (contact_id, subject, body, scheduled_for, now),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_scheduled_emails(status="scheduled"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, c.name, c.email, c.company
        FROM scheduled_emails s
        JOIN contacts c ON c.id = s.contact_id
        WHERE s.status = %s
        ORDER BY s.scheduled_for ASC
    """, (status,))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


def mark_scheduled_email(schedule_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE scheduled_emails SET status = %s WHERE id = %s", (status, schedule_id))
    conn.commit()
    cur.close()
    conn.close()


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
        FROM events
        WHERE event_type IN ('sent', 'bounced', 'replied')
        GROUP BY d, event_type ORDER BY d
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
