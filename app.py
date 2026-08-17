"""
Prototype UX: upload a CSV/Excel sheet, review sector classification,
send a throttled batch, watch a live dashboard. Run with:

    streamlit run app.py

Credentials come from environment variables (see .env.example) --
never hardcode your app password in this file.
"""

from dotenv import load_dotenv
load_dotenv()  # must run before importing db/sender, which read env vars at import time

import os
import pandas as pd
import streamlit as st

# On Streamlit Community Cloud, credentials come from st.secrets, not a
# .env file. Copy them into the environment so db.py / sender.py can keep
# using plain os.getenv() everywhere, whether run locally or hosted.
try:
    for key, value in st.secrets.items():
        os.environ.setdefault(key, str(value))
except Exception:
    pass

import db
import classifier
import templates
import sender

st.set_page_config(page_title="Outreach prototype", layout="wide")
db.init_db()

SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")

st.title("Outreach prototype")

tab_upload, tab_send, tab_dashboard = st.tabs(["Upload contacts", "Compose & send", "Dashboard"])

# ---------------------------------------------------------------- Upload tab
with tab_upload:
    st.subheader("Upload your contact sheet")
    st.caption("CSV or Excel. Expected columns: name, email, company. A 'sector' column is optional -- "
               "if missing, it's classified locally from the company name.")

    uploaded = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

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
                    lambda r: r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip()
                    else classifier.classify(r["company"]),
                    axis=1,
                )

            st.write(f"{len(df)} rows parsed. Review sector assignment below, edit if needed:")
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

            if st.button("Save to contact list", type="primary"):
                rows = edited.to_dict("records")
                inserted, skipped = db.upsert_contacts(rows)
                st.success(f"Saved {inserted} contacts. Skipped {skipped} (duplicates or invalid email).")

# ------------------------------------------------------------------ Send tab
with tab_send:
    st.subheader("Compose & send")

    if not SENDER_EMAIL or not APP_PASSWORD:
        st.warning("Set SENDER_EMAIL and SENDER_APP_PASSWORD as environment variables before sending. "
                   "See .env.example.")

    pending = db.get_contacts(status="pending")
    st.write(f"{len(pending)} contacts pending outreach.")

    if pending:
        sample = pending[0]
        subject, body = templates.render(sample)
        with st.expander(f"Preview for {sample['name']} ({sample['sector']})"):
            st.text_input("Subject", subject, disabled=True)
            st.text_area("Body", body, height=220, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            delay = st.number_input("Delay between sends (seconds)", min_value=10, value=60, step=10)
        with col2:
            daily_cap = st.number_input("Max sends this run", min_value=1, value=30, step=5)

        st.caption("Start small. 20-30 contacts is the right size for a first real test.")

        if st.button("Send test to myself"):
            try:
                sender.send_one(SENDER_EMAIL, APP_PASSWORD, SENDER_EMAIL, subject, body)
                st.success("Test email sent -- check your inbox.")
            except Exception as e:
                st.error(f"Send failed: {e}")

        if st.button("Start sending batch", type="primary"):
            progress = st.progress(0)
            status_line = st.empty()

            def on_progress(count, last_email):
                progress.progress(min(count / daily_cap, 1.0))
                status_line.write(f"Sent {count}/{daily_cap} -- last: {last_email}")

            sent = sender.send_batch(
                SENDER_EMAIL, APP_PASSWORD, pending, templates.render,
                delay_seconds=delay, daily_cap=daily_cap, progress_callback=on_progress,
            )
            st.success(f"Batch complete. {sent} contacts processed.")

# ------------------------------------------------------------- Dashboard tab
with tab_dashboard:
    st.subheader("Dashboard")

    if st.button("Check for replies & bounces"):
        if not SENDER_EMAIL or not APP_PASSWORD:
            st.warning("Set SENDER_EMAIL and SENDER_APP_PASSWORD to check your inbox.")
        else:
            result = sender.check_replies_and_bounces(SENDER_EMAIL, APP_PASSWORD)
            st.info(f"Found {result['replies_found']} new replies, {result['bounces_found']} new bounces.")

    metrics = db.get_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total contacts", metrics["total_contacts"])
    c2.metric("Sent", metrics["sent"])
    c3.metric("Bounced", metrics["bounced"])
    c4.metric("Replied", metrics["replied"])

    if metrics["sent"] > 0:
        rate = round(metrics["bounced"] / metrics["sent"] * 100, 1)
        st.caption(f"Bounce rate: {rate}%")

    if metrics["daily"]:
        daily_df = pd.DataFrame(metrics["daily"])
        pivot = daily_df.pivot_table(index="d", columns="event_type", values="c", fill_value=0)
        st.bar_chart(pivot)
    else:
        st.caption("No sends yet -- the chart fills in once you start sending.")
