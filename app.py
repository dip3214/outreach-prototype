"""
Outreach dashboard for Streamlit.

The app keeps the existing upload/send workflow, but makes the main
experience an outbound email history dashboard inspired by modern email
platforms such as Resend.
"""

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

# ---------------------------------------------------------------------------
# Styling
st.markdown(
    """
    <style>
    .stApp { background: #ffffff; }
    [data-testid="stSidebar"] { border-right: 1px solid #e8e8e8; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }
    .brand { font-size: 1.05rem; font-weight: 700; margin-bottom: 1.5rem; }
    .top-title { font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.2rem; }
    .muted { color: #737373; font-size: 0.9rem; }
    .metric-card { border: 1px solid #e9e9e9; border-radius: 14px; padding: 16px 18px; background: #fff; }
    .metric-label { font-size: 0.82rem; color: #737373; margin-bottom: 6px; }
    .metric-value { font-size: 1.65rem; font-weight: 700; }
    .status-pill { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 0.75rem; }
    .section-box { border: 1px solid #ececec; border-radius: 14px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar navigation
with st.sidebar:
    st.markdown('<div class="brand">✉ Outreach</div>', unsafe_allow_html=True)
    page = st.radio(
        "",
        ["Emails", "Broadcasts", "Automations", "Templates", "Audience", "Metrics"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Connected sender")
    st.write(SENDER_EMAIL or "Sender not configured")

# ---------------------------------------------------------------------------
# Helpers

def _events_frame():
    rows = db.get_contacts()
    if not rows:
        return pd.DataFrame()

    events = []
    try:
        import psycopg2
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                e.id,
                e.contact_id,
                e.event_type,
                e.detail,
                e.timestamp,
                c.name,
                c.email,
                c.company,
                c.sector
            FROM events e
            JOIN contacts c ON c.id = e.contact_id
            ORDER BY e.timestamp DESC
        """)
        events = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
    except Exception:
        return pd.DataFrame()

    return pd.DataFrame(events)


def _format_sent(ts):
    if not ts:
        return ""
    try:
        dt = pd.to_datetime(ts, utc=True).to_pydatetime()
        delta = datetime.now(timezone.utc) - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 7:
            return f"{days}d ago"
        return dt.strftime("%d %b %Y")
    except Exception:
        return str(ts)

# ---------------------------------------------------------------------------
# Emails page: Resend-style outbound history
if page == "Emails":
    st.markdown('<div class="top-title">Emails</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted">Review every outbound email and its delivery status.</div>', unsafe_allow_html=True)
    st.write("")

    events_df = _events_frame()
    sent_df = events_df[events_df["event_type"].astype(str).str.lower().isin(["sent", "bounced", "replied"])] if not events_df.empty else pd.DataFrame()

    # Tabs mirror the reference structure, with Sending first.
    mode = st.segmented_control("", ["Sending", "Receiving"], default="Sending", label_visibility="collapsed")

    if mode == "Receiving":
        st.info("Receiving is kept as a secondary view. Use the dashboard controls on the Sending tab to check for replies and bounces.")

    col_search, col_range, col_status, col_key, col_download = st.columns([2.2, 1, 1, 1, 0.35])
    with col_search:
        search = st.text_input("Search", placeholder="Search recipient, company, subject...", label_visibility="collapsed")
    with col_range:
        date_range = st.selectbox("Date", ["Last 15 days", "Last 30 days", "All time"], label_visibility="collapsed")
    with col_status:
        status_filter = st.selectbox("Status", ["All Statuses", "Delivered", "Bounced", "Replied"], label_visibility="collapsed")
    with col_key:
        st.selectbox("API key", ["All API keys"], label_visibility="collapsed")
    with col_download:
        csv_bytes = sent_df.to_csv(index=False).encode("utf-8") if not sent_df.empty else b""
        st.download_button("↓", data=csv_bytes, file_name="outbound-history.csv", mime="text/csv", disabled=not bool(csv_bytes), help="Download outbound history")

    filtered = sent_df.copy()
    if not filtered.empty:
        filtered["timestamp_dt"] = pd.to_datetime(filtered["timestamp"], utc=True, errors="coerce")
        if date_range != "All time":
            days = 15 if date_range == "Last 15 days" else 30
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            filtered = filtered[filtered["timestamp_dt"] >= cutoff]
        if status_filter != "All Statuses":
            target = status_filter.lower().rstrip("ed") if status_filter == "Delivered" else status_filter.lower()
            if status_filter == "Delivered":
                target = "sent"
            filtered = filtered[filtered["event_type"].str.lower() == target]
        if search:
            mask = (
                filtered["email"].astype(str).str.contains(search, case=False, na=False)
                | filtered["name"].astype(str).str.contains(search, case=False, na=False)
                | filtered["company"].astype(str).str.contains(search, case=False, na=False)
                | filtered["detail"].astype(str).str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]
        filtered = filtered.sort_values("timestamp_dt", ascending=False)

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)
    st.markdown("**To**　　　　　　　　　　　　　　　　 **Status**　　　　 **Subject / Detail**　　　　　　　　　　　 **Sent**")

    if filtered.empty:
        st.caption("No outbound email history yet. Send a test or batch from Broadcasts to start building history.")
    else:
        for _, row in filtered.iterrows():
            event = str(row.get("event_type", "")).lower()
            label = "Delivered" if event == "sent" else event.capitalize()
            recipient = row.get("email") or "Unknown recipient"
            detail = row.get("detail") or "Outbound email"
            sent = _format_sent(row.get("timestamp"))
            status_text = f"`{label}`"
            line = st.columns([2.2, 1, 3.6, 0.8])
            with line[0]:
                st.write(recipient)
            with line[1]:
                st.write(status_text)
            with line[2]:
                st.write(detail)
            with line[3]:
                st.write(sent)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.subheader("Overview")
    metrics = db.get_metrics()
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total contacts", metrics["total_contacts"])
    with m2:
        st.metric("Delivered", metrics["sent"])
    with m3:
        st.metric("Bounced", metrics["bounced"])
    with m4:
        st.metric("Replied", metrics["replied"])

    if st.button("Check for replies & bounces"):
        if not SENDER_EMAIL or not APP_PASSWORD:
            st.warning("Set SENDER_EMAIL and SENDER_APP_PASSWORD before checking the mailbox.")
        else:
            result = sender.check_replies_and_bounces(SENDER_EMAIL, APP_PASSWORD)
            st.success(f"Found {result['replies_found']} new replies and {result['bounces_found']} new bounces.")
            st.rerun()

# ---------------------------------------------------------------------------
# Broadcasts: preserve existing compose/send flow
elif page == "Broadcasts":
    st.title("Broadcasts")
    st.caption("Upload contacts, preview outreach, and send a controlled batch.")

    tab_upload, tab_send = st.tabs(["Upload contacts", "Compose & send"])

    with tab_upload:
        uploaded = st.file_uploader("Choose a CSV or Excel contact sheet", type=["csv", "xlsx", "xls"])
        if uploaded:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            df.columns = [c.strip().lower() for c in df.columns]
            missing = [c for c in ["name", "email", "company"] if c not in df.columns]
            if missing:
                st.error(f"Missing required column(s): {', '.join(missing)}")
            else:
                if "sector" not in df.columns:
                    df["sector"] = df["company"].apply(classifier.classify)
                else:
                    df["sector"] = df.apply(
                        lambda r: r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),
                        axis=1,
                    )
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
                progress = st.progress(0)
                status_line = st.empty()
                def on_progress(count, last_email):
                    progress.progress(min(count / daily_cap, 1.0))
                    status_line.write(f"Sent {count}/{daily_cap} — last: {last_email}")
                sent = sender.send_batch(
                    SENDER_EMAIL, APP_PASSWORD, pending, templates.render,
                    delay_seconds=delay, daily_cap=daily_cap, progress_callback=on_progress,
                )
                st.success(f"Batch complete. {sent} contacts processed.")
                st.rerun()

# ---------------------------------------------------------------------------
# Placeholder pages keep the dashboard structure clean and extensible.
elif page == "Automations":
    st.title("Automations")
    st.caption("Scheduled outreach workflows can be added here next.")
    st.info("The current prototype focuses on outbound email history and controlled batch sending.")

elif page == "Templates":
    st.title("Templates")
    st.caption("Reusable outreach templates.")
    st.write("Your current rendering logic remains in `templates.py`.")

elif page == "Audience":
    st.title("Audience")
    contacts = db.get_contacts()
    st.dataframe(pd.DataFrame(contacts), use_container_width=True, hide_index=True)

elif page == "Metrics":
    st.title("Metrics")
    metrics = db.get_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contacts", metrics["total_contacts"])
    c2.metric("Delivered", metrics["sent"])
    c3.metric("Bounced", metrics["bounced"])
    c4.metric("Replied", metrics["replied"])
    if metrics["daily"]:
        daily_df = pd.DataFrame(metrics["daily"])
        pivot = daily_df.pivot_table(index="d", columns="event_type", values="c", fill_value=0)
        st.bar_chart(pivot)
