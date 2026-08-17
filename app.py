"""Outreach: focused email operations dashboard."""

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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
IST = ZoneInfo("Asia/Kolkata")

# ---------------------------------------------------------------------------
# Visual system: white canvas, graphite text, blue primary, restrained status colors.
st.markdown("""
<style>
.stApp { background:#f8fafc; color:#111827; }
[data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #e5e7eb; }
[data-testid="stSidebar"] > div:first-child { padding:1.2rem .8rem; }
.brand { font-size:1.15rem; font-weight:750; color:#111827; margin:.1rem .45rem 1.25rem; }
.page-title { font-size:2rem; line-height:1.1; font-weight:750; letter-spacing:-.035em; color:#111827; }
.page-subtitle { color:#6b7280; font-size:.92rem; margin:.35rem 0 1.35rem; }
.card { background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:18px; }
.metric-card { background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:17px 18px; }
.metric-label { color:#6b7280; font-size:.8rem; font-weight:600; }
.metric-value { color:#111827; font-size:1.75rem; font-weight:750; margin-top:4px; }
.metric-note { color:#9ca3af; font-size:.75rem; margin-top:2px; }
.section-title { font-size:1rem; font-weight:700; color:#111827; margin:1.2rem 0 .65rem; }
.small-muted { color:#6b7280; font-size:.82rem; }
.status-sent { color:#15803d; font-weight:650; }
.status-bounced { color:#dc2626; font-weight:650; }
.status-replied { color:#7c3aed; font-weight:650; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e5e7eb; border-radius:14px; padding:12px 16px; }
button[kind="primary"] { background:#2563eb; border-color:#2563eb; }
</style>
""", unsafe_allow_html=True)

# Deliver due scheduled messages whenever the Streamlit app is active.
if SENDER_EMAIL and APP_PASSWORD:
    try:
        sender.send_due_scheduled(SENDER_EMAIL, APP_PASSWORD)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Only three product areas.
with st.sidebar:
    st.markdown('<div class="brand">✉ Outreach</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["Dashboard", "Emails", "Customers"], label_visibility="collapsed")
    st.divider()
    st.caption("Sender")
    st.write(SENDER_EMAIL or "Not configured")


def event_history():
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
        seconds = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
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


def metric_card(label, value, note, accent):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note" style="color:{accent}">{note}</div></div>',
        unsafe_allow_html=True,
    )


def send_custom(contact, subject, body):
    if not SENDER_EMAIL or not APP_PASSWORD:
        st.error("Configure SENDER_EMAIL and SENDER_APP_PASSWORD in Streamlit Secrets first.")
        return False
    try:
        sender.send_one(SENDER_EMAIL, APP_PASSWORD, contact["email"], subject, body)
        db.log_event(contact["id"], "sent", subject=subject)
        return True
    except Exception as exc:
        db.log_event(contact["id"], "bounced", str(exc), subject)
        st.error(f"Send failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# DASHBOARD
if page == "Dashboard":
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">A simple view of your outbound email performance.</div>', unsafe_allow_html=True)

    metrics = db.get_metrics()
    a, b, c = st.columns(3)
    with a: metric_card("Mail sent", metrics["sent"], "Total delivered sends", "#2563eb")
    with b: metric_card("Bounce", metrics["bounced"], "Delivery failures", "#dc2626")
    with c: metric_card("Reply", metrics["replied"], "Contacts that replied", "#7c3aed")

    st.markdown('<div class="section-title">Email activity</div>', unsafe_allow_html=True)
    if metrics["daily"]:
        chart = pd.DataFrame(metrics["daily"])
        chart["d"] = pd.to_datetime(chart["d"])
        chart = chart.pivot_table(index="d", columns="event_type", values="c", aggfunc="sum", fill_value=0).sort_index()
        for col in ["sent", "bounced", "replied"]:
            if col not in chart.columns: chart[col] = 0
        st.line_chart(chart[["sent", "bounced", "replied"]], height=330)
    else:
        st.markdown('<div class="card small-muted">Your activity graph will appear after the first email is sent.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# EMAILS: history + manual compose + future scheduling
elif page == "Emails":
    st.markdown('<div class="page-title">Emails</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Send, schedule and review every outbound email from one place.</div>', unsafe_allow_html=True)

    tab_history, tab_compose, tab_campaign = st.tabs(["History", "Compose", "CSV campaign"])

    with tab_history:
        history = event_history()
        if not history.empty:
            history = history[history["event_type"].astype(str).str.lower().isin(["sent", "bounced", "replied"])].copy()

        f1, f2, f3, f4 = st.columns([2.2, 1, 1, .5])
        with f1: search = st.text_input("Search", placeholder="Search recipient, company or subject", label_visibility="collapsed")
        with f2: period = st.selectbox("Period", ["Last 15 days", "Last 30 days", "All time"], label_visibility="collapsed")
        with f3: status = st.selectbox("Status", ["All", "Delivered", "Bounced", "Replied"], label_visibility="collapsed")
        with f4:
            csv = history.to_csv(index=False).encode("utf-8") if not history.empty else b""
            st.download_button("↓", csv, "email-history.csv", "text/csv", disabled=not bool(csv), help="Download email history")

        filtered = history.copy()
        if not filtered.empty:
            filtered["timestamp_dt"] = pd.to_datetime(filtered["timestamp"], utc=True, errors="coerce")
            if period != "All time":
                cutoff = datetime.now(timezone.utc) - timedelta(days=15 if period == "Last 15 days" else 30)
                filtered = filtered[filtered["timestamp_dt"] >= cutoff]
            if status != "All":
                filtered = filtered[filtered["event_type"].str.lower() == ("sent" if status == "Delivered" else status.lower())]
            if search:
                mask = pd.Series(False, index=filtered.index)
                for field in ["email", "name", "company", "subject", "detail"]:
                    mask |= filtered[field].fillna("").astype(str).str.contains(search, case=False, na=False)
                filtered = filtered[mask]
            filtered = filtered.sort_values("timestamp_dt", ascending=False)

        if filtered.empty:
            st.info("No outbound email history yet.")
        else:
            header = st.columns([2.25, 1, 3.8, .8])
            header[0].markdown("**TO**")
            header[1].markdown("**STATUS**")
            header[2].markdown("**SUBJECT**")
            header[3].markdown("**SENT**")
            for _, row in filtered.iterrows():
                cols = st.columns([2.25, 1, 3.8, .8])
                event = str(row["event_type"]).lower()
                label = "Delivered" if event == "sent" else event.capitalize()
                cols[0].write(row.get("email", ""))
                cols[1].markdown(f'<span class="status-{event}">{label}</span>', unsafe_allow_html=True)
                cols[2].write(row.get("subject") or row.get("detail") or "Outbound email")
                cols[3].write(relative_time(row.get("timestamp")))
                st.divider()

        if st.button("Sync replies & bounces"):
            if not SENDER_EMAIL or not APP_PASSWORD:
                st.warning("Configure the sender credentials first.")
            else:
                result = sender.check_replies_and_bounces(SENDER_EMAIL, APP_PASSWORD)
                st.success(f"Synced {result['replies_found']} replies and {result['bounces_found']} bounces.")
                st.rerun()

    with tab_compose:
        contacts = db.get_contacts()
        if not contacts:
            st.info("Add a customer first from Customers.")
        else:
            options = {f"{c['name']} — {c['email']}": c for c in contacts}
            selected_label = st.selectbox("Customer", list(options.keys()))
            contact = options[selected_label]
            mode = st.radio("Message", ["Custom email", "Use classified template"], horizontal=True)

            if mode == "Use classified template":
                subject, body = templates.render(contact)
            else:
                subject = st.text_input("Subject", placeholder="Write your subject")
                body = st.text_area("Email", height=250, placeholder="Write your email...")

            st.caption(f"Customer sector: {contact.get('sector') or 'general'}")
            send_now, schedule = st.columns(2)
            with send_now:
                if st.button("Send now", type="primary", use_container_width=True):
                    if not subject.strip() or not body.strip():
                        st.warning("Add a subject and message first.")
                    elif send_custom(contact, subject, body):
                        st.success(f"Email sent to {contact['email']}.")
                        st.rerun()
            with schedule:
                if st.button("Schedule for later", use_container_width=True):
                    if not subject.strip() or not body.strip():
                        st.warning("Add a subject and message first.")
                    else:
                        st.session_state["schedule_ready"] = True

            if st.session_state.get("schedule_ready"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Schedule this email**")
                d = st.date_input("Date", value=datetime.now(IST).date(), min_value=datetime.now(IST).date())
                t = st.time_input("Time (India)", value=(datetime.now(IST) + timedelta(hours=1)).replace(second=0, microsecond=0).time())
                if st.button("Confirm schedule", type="primary"):
                    local_dt = datetime.combine(d, t).replace(tzinfo=IST)
                    db.schedule_email(contact["id"], subject, body, local_dt.astimezone(timezone.utc).isoformat())
                    st.session_state["schedule_ready"] = False
                    st.success(f"Scheduled for {local_dt.strftime('%d %b %Y, %I:%M %p')} IST.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            scheduled = db.get_scheduled_emails("scheduled")
            if scheduled:
                st.markdown('<div class="section-title">Upcoming scheduled emails</div>', unsafe_allow_html=True)
                for item in scheduled:
                    when = pd.to_datetime(item["scheduled_for"], utc=True).tz_convert("Asia/Kolkata").strftime("%d %b %Y, %I:%M %p")
                    st.write(f"**{item['name']}** · {item['email']} · {when} IST · {item['subject']}")

    with tab_campaign:
        st.markdown("**Classified CSV campaign**")
        st.caption("Upload contacts, review/edit their sector classification, then use the sector-aware template for the campaign.")
        uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], key="campaign_upload")
        if uploaded:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [str(c).strip().lower() for c in df.columns]
            missing = [c for c in ["name", "email", "company"] if c not in df.columns]
            if missing:
                st.error(f"Missing required column(s): {', '.join(missing)}")
            else:
                if "sector" not in df.columns:
                    df["sector"] = df["company"].apply(classifier.classify)
                else:
                    df["sector"] = df.apply(lambda r: r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]), axis=1)
                edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                if st.button("Save classified customers", type="primary"):
                    inserted, skipped = db.upsert_contacts(edited.to_dict("records"))
                    st.success(f"Saved {inserted} customers. Skipped {skipped} duplicates/invalid rows.")
                    st.session_state["campaign_contacts"] = edited.to_dict("records")

        campaign_contacts = st.session_state.get("campaign_contacts", [])
        if campaign_contacts:
            sector = st.selectbox("Send to sector", ["All sectors"] + sorted({str(x.get("sector") or "general") for x in campaign_contacts}))
            selected = campaign_contacts if sector == "All sectors" else [x for x in campaign_contacts if (x.get("sector") or "general") == sector]
            st.write(f"{len(selected)} customer(s) selected.")
            if selected:
                preview = selected[0]
                preview_subject, preview_body = templates.render(preview)
                with st.expander(f"Preview: {preview['name']} · {preview.get('sector') or 'general'}"):
                    st.text_input("Subject", preview_subject, disabled=True, key="campaign_subject_preview")
                    st.text_area("Body", preview_body, height=200, disabled=True, key="campaign_body_preview")
                delay = st.number_input("Delay between emails (seconds)", min_value=10, value=60, step=10)
                cap = st.number_input("Maximum emails this run", min_value=1, value=min(30, len(selected)), step=1)
                if st.button("Send classified campaign", type="primary"):
                    email_map = {c["email"].lower(): c for c in db.get_contacts()}
                    db_contacts = [email_map[x["email"].lower()] for x in selected if x.get("email", "").lower() in email_map]
                    progress = st.progress(0); status_line = st.empty()
                    def progress_callback(count, last_email):
                        progress.progress(min(count / cap, 1.0)); status_line.write(f"Sent {count}/{cap} · {last_email}")
                    sent_count = sender.send_batch(SENDER_EMAIL, APP_PASSWORD, db_contacts, templates.render, delay_seconds=delay, daily_cap=cap, progress_callback=progress_callback)
                    st.success(f"Campaign complete. {sent_count} customer(s) processed.")
                    st.session_state.pop("campaign_contacts", None)
                    st.rerun()

# ---------------------------------------------------------------------------
# CUSTOMERS: manual entry + CSV + complete downloadable history
elif page == "Customers":
    st.markdown('<div class="page-title">Customers</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Add customers manually or import a CSV. Every customer keeps a downloadable communication history.</div>', unsafe_allow_html=True)

    add_tab, import_tab, list_tab = st.tabs(["Add customer", "Import CSV", "Customer list"])

    with add_tab:
        with st.form("add_customer"):
            name = st.text_input("Name")
            email_addr = st.text_input("Email")
            company = st.text_input("Company")
            sector_options = ["general", "healthcare", "fintech", "saas_tech", "manufacturing", "retail_ecom"]
            sector = st.selectbox("Sector", sector_options)
            submitted = st.form_submit_button("Add customer", type="primary")
            if submitted:
                if not name.strip() or not email_addr.strip() or "@" not in email_addr:
                    st.error("Name and a valid email are required.")
                else:
                    inserted, skipped = db.upsert_contacts([{"name": name, "email": email_addr, "company": company, "sector": sector}])
                    if inserted:
                        st.success("Customer added.")
                    else:
                        st.warning("That email already exists or is invalid.")

    with import_tab:
        st.markdown("**CSV format:** `name`, `email`, `company` — `sector` is optional and will be classified automatically.")
        uploaded = st.file_uploader("Upload customer CSV / Excel", type=["csv", "xlsx", "xls"], key="customer_import")
        if uploaded:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [str(c).strip().lower() for c in df.columns]
            missing = [c for c in ["name", "email", "company"] if c not in df.columns]
            if missing:
                st.error(f"Missing required column(s): {', '.join(missing)}")
            else:
                if "sector" not in df.columns:
                    df["sector"] = df["company"].apply(classifier.classify)
                else:
                    df["sector"] = df.apply(lambda r: r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]), axis=1)
                edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
                if st.button("Import customers", type="primary"):
                    inserted, skipped = db.upsert_contacts(edited.to_dict("records"))
                    st.success(f"Imported {inserted} customers. Skipped {skipped} duplicates/invalid rows.")

    with list_tab:
        contacts = db.get_contacts()
        if not contacts:
            st.info("No customers yet.")
        else:
            customer_df = pd.DataFrame(contacts)
            customer_df = customer_df[[c for c in ["id", "name", "email", "company", "sector", "status", "created_at"] if c in customer_df.columns]]
            st.dataframe(customer_df, use_container_width=True, hide_index=True)

            st.markdown('<div class="section-title">Customer history</div>', unsafe_allow_html=True)
            labels = {f"{c['name']} — {c['email']}": c["id"] for c in contacts}
            selected_label = st.selectbox("Customer", list(labels.keys()), key="history_customer")
            customer_id = labels[selected_label]
            history_rows = db.get_customer_history(customer_id)
            history_df = pd.DataFrame(history_rows)
            if history_df.empty:
                st.caption("No communication history for this customer yet.")
            else:
                display_cols = [c for c in ["timestamp", "event_type", "subject", "detail"] if c in history_df.columns]
                st.dataframe(history_df[display_cols], use_container_width=True, hide_index=True)
                st.download_button(
                    "Download customer history",
                    history_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"{selected_label.split(' — ')[0].replace(' ', '_')}-history.csv",
                    mime="text/csv",
                    type="primary",
                )
