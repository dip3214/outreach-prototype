"""Clean Resend-style outbound email dashboard for Streamlit."""

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass

import db
import classifier
import templates
import sender

st.set_page_config(page_title="Outreach", page_icon="✉", layout="wide", initial_sidebar_state="expanded")
db.init_db()

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")

st.markdown("""
<style>
.stApp { background:#fff; }
[data-testid="stSidebar"] { border-right:1px solid #e7e7e7; }
.brand { font-size:1.05rem; font-weight:700; margin:0 0 1.4rem 0; }
.top-title { font-size:2rem; font-weight:700; letter-spacing:-.025em; margin-bottom:.15rem; }
.muted { color:#737373; font-size:.9rem; }
.section-box { border:1px solid #e7e7e7; border-radius:14px; overflow:hidden; }
.email-head { background:#f7f7f7; border-bottom:1px solid #e7e7e7; padding:11px 14px; font-size:.78rem; font-weight:600; color:#666; }
.email-row { border-bottom:1px solid #eeeeee; padding:12px 14px; font-size:.88rem; }
.email-row:last-child { border-bottom:0; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">✉ Outreach</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["Emails", "Broadcasts", "Automations", "Templates", "Audience", "Metrics"], label_visibility="collapsed")
    st.divider()
    st.caption("Connected sender")
    st.write(SENDER_EMAIL or "Sender not configured")


def get_event_history():
    try:
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.contact_id, e.event_type, e.detail, e.subject, e.timestamp,
                   c.name, c.email, c.company, c.sector
            FROM events e
            JOIN contacts c ON c.id = e.contact_id
            ORDER BY e.timestamp DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def relative_time(ts):
    try:
        dt = pd.to_datetime(ts, utc=True).to_pydatetime()
        seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
        if seconds < 60: return "just now"
        minutes = seconds // 60
        if minutes < 60: return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24: return f"{hours}h ago"
        days = hours // 24
        if days < 7: return f"{days}d ago"
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(ts or "")


if page == "Emails":
    st.markdown('<div class="top-title">Emails</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">A complete history of outbound email from your account.</div>', unsafe_allow_html=True)
    st.write("")

    mode = st.radio("", ["Sending", "Receiving"], horizontal=True, label_visibility="collapsed")
    if mode == "Receiving":
        st.info("Receiving is available as a secondary view. Use 'Check for replies & bounces' below to sync incoming activity.")

    history = get_event_history()
    if not history.empty:
        history = history[history["event_type"].astype(str).str.lower().isin(["sent", "bounced", "replied"])].copy()

    c1, c2, c3, c4, c5 = st.columns([2.2, 1, 1, 1, .45])
    with c1:
        search = st.text_input("Search", placeholder="Search...", label_visibility="collapsed")
    with c2:
        period = st.selectbox("Period", ["Last 15 days", "Last 30 days", "All time"], label_visibility="collapsed")
    with c3:
        status = st.selectbox("Status", ["All Statuses", "Delivered", "Bounced", "Replied"], label_visibility="collapsed")
    with c4:
        st.selectbox("API key", ["All API keys"], label_visibility="collapsed")
    with c5:
        csv = history.to_csv(index=False).encode("utf-8") if not history.empty else b""
        st.download_button("↓", csv, "outbound-email-history.csv", "text/csv", disabled=not bool(csv), help="Download history")

    filtered = history.copy()
    if not filtered.empty:
        filtered["timestamp_dt"] = pd.to_datetime(filtered["timestamp"], utc=True, errors="coerce")
        if period != "All time":
            cutoff = datetime.now(timezone.utc) - timedelta(days=15 if period == "Last 15 days" else 30)
            filtered = filtered[filtered["timestamp_dt"] >= cutoff]
        if status != "All Statuses":
            target = "sent" if status == "Delivered" else status.lower()
            filtered = filtered[filtered["event_type"].str.lower() == target]
        if search:
            fields = ["email", "name", "company", "subject", "detail"]
            mask = pd.Series(False, index=filtered.index)
            for field in fields:
                mask |= filtered[field].fillna("").astype(str).str.contains(search, case=False, na=False)
            filtered = filtered[mask]
        filtered = filtered.sort_values("timestamp_dt", ascending=False)

    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    h = st.columns([2.3, 1.05, 4.0, .85])
    h[0].markdown('<div class="email-head">TO</div>', unsafe_allow_html=True)
    h[1].markdown('<div class="email-head">STATUS</div>', unsafe_allow_html=True)
    h[2].markdown('<div class="email-head">SUBJECT</div>', unsafe_allow_html=True)
    h[3].markdown('<div class="email-head">SENT</div>', unsafe_allow_html=True)

    if filtered.empty:
        st.caption("No outbound emails match your filters yet.")
    else:
        for _, row in filtered.iterrows():
            event = str(row.get("event_type", "")).lower()
            label = "Delivered" if event == "sent" else event.capitalize()
            recipient = row.get("email") or "Unknown recipient"
            subject = row.get("subject") or row.get("detail") or "Outbound email"
            sent = relative_time(row.get("timestamp"))
            cols = st.columns([2.3, 1.05, 4.0, .85])
            cols[0].write(recipient)
            cols[1].write(label)
            cols[2].write(subject)
            cols[3].write(sent)
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    metrics = db.get_metrics()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total contacts", metrics["total_contacts"])
    m2.metric("Delivered", metrics["sent"])
    m3.metric("Bounced", metrics["bounced"])
    m4.metric("Replied", metrics["replied"])

    if st.button("Check for replies & bounces"):
        if not SENDER_EMAIL or not APP_PASSWORD:
            st.warning("Set SENDER_EMAIL and SENDER_APP_PASSWORD before checking the mailbox.")
        else:
            result = sender.check_replies_and_bounces(SENDER_EMAIL, APP_PASSWORD)
            st.success(f"Found {result['replies_found']} new replies and {result['bounces_found']} new bounces.")
            st.rerun()

elif page == "Broadcasts":
    st.title("Broadcasts")
    st.caption("Upload contacts, preview outreach, and send a controlled batch.")
    tab_upload, tab_send = st.tabs(["Upload contacts", "Compose & send"])

    with tab_upload:
        uploaded = st.file_uploader("Choose a CSV or Excel contact sheet", type=["csv", "xlsx", "xls"])
        if uploaded:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [c.strip().lower() for c in df.columns]
            missing = [c for c in ["name", "email", "company"] if c not in df.columns]
            if missing:
                st.error(f"Missing required column(s): {', '.join(missing)}")
            else:
                if "sector" not in df.columns:
                    df["sector"] = df["company"].apply(classifier.classify)
                edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                if st.button("Save to contact list", type="primary"):
                    inserted, skipped = db.upsert_contacts(edited.to_dict("records"))
                    st.success(f"Saved {inserted} contacts. Skipped {skipped} duplicates/invalid rows.")

    with tab_send:
        pending = db.get_contacts(status="pending")
        st.write(f"{len(pending)} contacts pending outreach.")
        if pending:
            sample = pending[0]
            subject, body = templates.render(sample)
            with st.expander(f"Preview for {sample['name']} ({sample['sector']})"):
                st.text_input("Subject", subject, disabled=True)
                st.text_area("Body", body, height=220, disabled=True)
            delay = st.number_input("Delay between sends (seconds)", min_value=10, value=60, step=10)
            daily_cap = st.number_input("Max sends this run", min_value=1, value=30, step=5)
            if st.button("Send test to myself"):
                try:
                    sender.send_one(SENDER_EMAIL, APP_PASSWORD, SENDER_EMAIL, subject, body)
                    st.success("Test email sent — check your inbox.")
                except Exception as e:
                    st.error(f"Send failed: {e}")
            if st.button("Start sending batch", type="primary"):
                progress = st.progress(0); status_line = st.empty()
                def on_progress(count, last_email):
                    progress.progress(min(count / daily_cap, 1.0)); status_line.write(f"Sent {count}/{daily_cap} — last: {last_email}")
                sent = sender.send_batch(SENDER_EMAIL, APP_PASSWORD, pending, templates.render, delay_seconds=delay, daily_cap=daily_cap, progress_callback=on_progress)
                st.success(f"Batch complete. {sent} contacts processed.")
                st.rerun()

elif page == "Automations":
    st.title("Automations")
    st.caption("Scheduled outreach workflows can be added here next.")
    st.info("The current prototype focuses on outbound history and controlled batch sending.")

elif page == "Templates":
    st.title("Templates")
    st.caption("Reusable outreach templates.")
    st.write("Current rendering logic remains in templates.py.")

elif page == "Audience":
    st.title("Audience")
    st.dataframe(pd.DataFrame(db.get_contacts()), use_container_width=True, hide_index=True)

elif page == "Metrics":
    st.title("Metrics")
    metrics = db.get_metrics()
    a, b, c, d = st.columns(4)
    a.metric("Contacts", metrics["total_contacts"])
    b.metric("Delivered", metrics["sent"])
    c.metric("Bounced", metrics["bounced"])
    d.metric("Replied", metrics["replied"])
    if metrics["daily"]:
        daily_df = pd.DataFrame(metrics["daily"])
        st.bar_chart(daily_df.pivot_table(index="d", columns="event_type", values="c", fill_value=0))
