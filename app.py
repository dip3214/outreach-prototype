"""Outreach - simple, polished outbound email workspace."""
from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import altair as alt
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

# ------------------------------ visual system ------------------------------
st.markdown("""
<style>
.stApp { background:#f7f8fa; color:#15171a; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e7e9ed; }
[data-testid="stSidebar"] > div:first-child { padding:24px 14px; }
.brand { display:flex; align-items:center; gap:9px; font-size:1.18rem; font-weight:800; color:#15171a; margin:2px 8px 26px; }
.brand-mark { width:30px; height:30px; border-radius:9px; background:#2563eb; color:#fff; display:inline-flex; align-items:center; justify-content:center; font-weight:800; }
.page-title { font-size:2rem; line-height:1.1; font-weight:800; letter-spacing:-.04em; margin-top:4px; }
.page-subtitle { color:#6b7280; font-size:.92rem; margin:6px 0 24px; }
.card { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:18px; }
.metric { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:19px 20px; min-height:112px; }
.metric-label { color:#6b7280; font-size:.8rem; font-weight:650; }
.metric-value { font-size:1.85rem; font-weight:800; letter-spacing:-.03em; margin-top:7px; }
.metric-note { font-size:.74rem; color:#9ca3af; margin-top:3px; }
.section-title { font-size:1rem; font-weight:750; margin:26px 0 10px; }
.status-delivered { color:#15803d; font-weight:700; }
.status-bounced { color:#dc2626; font-weight:700; }
.status-replied { color:#7c3aed; font-weight:700; }
div[data-testid="stTabs"] button { font-weight:650; }
button[kind="primary"] { background:#2563eb; border-color:#2563eb; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">O</span>Outreach</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["Dashboard", "Emails", "Customers"], label_visibility="collapsed")
    st.divider()
    st.caption("Sending from")
    st.write(SENDER_EMAIL or "Not configured")


def history_df():
    try:
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.contact_id, e.event_type, e.detail, e.subject, e.timestamp,
                   c.name, c.email, c.company, c.sector
            FROM events e JOIN contacts c ON c.id=e.contact_id
            WHERE e.event_type IN ('sent','bounced','replied')
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
        seconds = max(0, int((datetime.now(timezone.utc)-dt).total_seconds()))
        if seconds < 60: return "just now"
        mins = seconds//60
        if mins < 60: return f"{mins}m ago"
        hours = mins//60
        if hours < 24: return f"{hours}h ago"
        days = hours//24
        if days < 7: return f"{days}d ago"
        return dt.strftime("%d %b %Y")
    except Exception:
        return ""


def send_one(contact, subject, body):
    if not SENDER_EMAIL or not APP_PASSWORD:
        st.error("Configure SENDER_EMAIL and SENDER_APP_PASSWORD in Streamlit Secrets.")
        return False
    try:
        sender.send_one(SENDER_EMAIL, APP_PASSWORD, contact["email"], subject, body)
        db.log_event(contact["id"], "sent", subject=subject)
        return True
    except Exception as exc:
        db.log_event(contact["id"], "bounced", str(exc), subject)
        return False


def customer_map():
    return {f"{c['name']} · {c['email']}": c for c in db.get_contacts()}


# ------------------------------ Dashboard ----------------------------------
if page == "Dashboard":
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your outbound email activity, at a glance.</div>', unsafe_allow_html=True)

    m = db.get_metrics()
    a,b,c = st.columns(3)
    for col, label, value, note in [(a,"Mail sent",m["sent"],"Successful outbound emails"),(b,"Bounce",m["bounced"],"Delivery failures"),(c,"Reply",m["replied"],"Replies detected")]:
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{value:,}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Email activity</div>', unsafe_allow_html=True)
    if m["daily"]:
        raw = pd.DataFrame(m["daily"])
        raw["date"] = pd.to_datetime(raw["d"]).dt.normalize()
        dates = pd.date_range(raw["date"].min(), raw["date"].max(), freq="D")
        series = raw.pivot_table(index="date", columns="event_type", values="c", aggfunc="sum", fill_value=0).reindex(dates, fill_value=0)
        for name in ["sent","bounced","replied"]:
            if name not in series.columns: series[name] = 0
        chart = series[["sent","bounced","replied"]].rename(columns={"sent":"Sent","bounced":"Bounce","replied":"Reply"}).reset_index(names="Date")
        long = chart.melt("Date", var_name="Status", value_name="Emails")
        graph = alt.Chart(long).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("Date:T", title=None, axis=alt.Axis(format="%d %b", labelColor="#6b7280", tickCount=7)),
            y=alt.Y("Emails:Q", title=None, axis=alt.Axis(labelColor="#6b7280", gridColor="#edf0f3"), scale=alt.Scale(nice=True, zero=True)),
            color=alt.Color("Status:N", title=None, scale=alt.Scale(domain=["Sent","Bounce","Reply"], range=["#2563eb","#dc2626","#7c3aed"])),
            tooltip=[alt.Tooltip("Date:T", title="Date"), alt.Tooltip("Status:N"), alt.Tooltip("Emails:Q")]
        ).properties(height=330).configure_view(stroke=None).configure_legend(orient="top", labelColor="#4b5563")
        st.altair_chart(graph, use_container_width=True)
    else:
        st.markdown('<div class="card" style="color:#6b7280">Send your first email and the activity graph will appear here.</div>', unsafe_allow_html=True)

# ------------------------------ Emails -------------------------------------
elif page == "Emails":
    st.markdown('<div class="page-title">Emails</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Send individually, schedule messages, or send a campaign to many customers at once.</div>', unsafe_allow_html=True)

    tab_history, tab_compose, tab_bulk = st.tabs(["History", "Compose", "Send to many"])

    with tab_history:
        h = history_df()
        f1,f2,f3,f4 = st.columns([2.4,1,1,.45])
        with f1: search=st.text_input("Search", placeholder="Search recipient, company or subject", label_visibility="collapsed")
        with f2: period=st.selectbox("Period",["Last 15 days","Last 30 days","All time"],label_visibility="collapsed")
        with f3: status=st.selectbox("Status",["All","Delivered","Bounced","Replied"],label_visibility="collapsed")
        with f4:
            data=h.to_csv(index=False).encode() if not h.empty else b""
            st.download_button("↓",data,"outreach-email-history.csv","text/csv",disabled=not bool(data),help="Download email history")
        f=h.copy()
        if not f.empty:
            f["dt"]=pd.to_datetime(f["timestamp"],utc=True,errors="coerce")
            if period!="All time": f=f[f["dt"]>=datetime.now(timezone.utc)-timedelta(days=15 if period=="Last 15 days" else 30)]
            if status!="All": f=f[f["event_type"]==("sent" if status=="Delivered" else status.lower())]
            if search:
                mask=pd.Series(False,index=f.index)
                for field in ["email","name","company","subject","detail"]: mask |= f[field].fillna("").astype(str).str.contains(search,case=False,na=False)
                f=f[mask]
        if f.empty:
            st.info("No outbound email history yet.")
        else:
            head=st.columns([2.4,1,3.6,.8]); [head[i].markdown(x) for i,x in enumerate(["**TO**","**STATUS**","**SUBJECT**","**SENT**"])]
            for _,r in f.sort_values("dt",ascending=False).iterrows():
                cols=st.columns([2.4,1,3.6,.8]); event=str(r["event_type"]); label="Delivered" if event=="sent" else event.capitalize()
                cols[0].write(r.get("email","")); cols[1].markdown(f'<span class="status-{label.lower()}">{label}</span>',unsafe_allow_html=True); cols[2].write(r.get("subject") or r.get("detail") or "Outbound email"); cols[3].write(relative_time(r.get("timestamp")))
                st.divider()
        if st.button("Sync replies & bounces"):
            if SENDER_EMAIL and APP_PASSWORD:
                result=sender.check_replies_and_bounces(SENDER_EMAIL,APP_PASSWORD); st.success(f"Synced {result['replies_found']} replies and {result['bounces_found']} bounces."); st.rerun()
            else: st.warning("Configure sender credentials first.")

    with tab_compose:
        contacts=customer_map()
        if not contacts: st.info("Add a customer from Customers first.")
        else:
            selected=st.selectbox("Customer",list(contacts.keys())); contact=contacts[selected]
            mode=st.radio("Message",["Write manually","Use classified template"],horizontal=True)
            if mode=="Write manually":
                subject=st.text_input("Subject",placeholder="Write your subject")
                body=st.text_area("Message",height=250,placeholder="Write your email...")
            else: subject,body=templates.render(contact); st.text_input("Subject",subject,disabled=True); st.text_area("Message",body,height=250,disabled=True)
            x,y=st.columns(2)
            with x:
                if st.button("Send now",type="primary",use_container_width=True):
                    if not subject.strip() or not body.strip(): st.warning("Add a subject and message first.")
                    elif send_one(contact,subject,body): st.success(f"Sent to {contact['email']}."); st.rerun()
            with y:
                if st.button("Schedule for later",use_container_width=True): st.session_state["schedule_open"]=True
            if st.session_state.get("schedule_open"):
                d=st.date_input("Date",datetime.now(IST).date(),min_value=datetime.now(IST).date())
                t=st.time_input("Time (India)",(datetime.now(IST)+timedelta(hours=1)).replace(second=0,microsecond=0).time())
                if st.button("Confirm schedule",type="primary"):
                    local=datetime.combine(d,t).replace(tzinfo=IST); db.schedule_email(contact["id"],subject,body,local.astimezone(timezone.utc).isoformat()); st.session_state["schedule_open"]=False; st.success("Email scheduled.")

    with tab_bulk:
        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.markdown("**Send many emails in one shot**")
        st.caption("Upload a customer list, automatically classify it, review the rows, choose the audience, preview the message, then send the whole batch.")
        uploaded=st.file_uploader("CSV or Excel",type=["csv","xlsx","xls"],key="bulk_upload")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded); df.columns=[str(c).strip().lower() for c in df.columns]
            missing=[x for x in ["name","email","company"] if x not in df.columns]
            if missing: st.error("Missing: "+", ".join(missing))
            else:
                if "sector" not in df.columns: df["sector"]=df["company"].apply(classifier.classify)
                else: df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
                edited=st.data_editor(df,num_rows="dynamic",use_container_width=True,key="bulk_editor")
                st.session_state["bulk_rows"]=edited.to_dict("records")
        rows=st.session_state.get("bulk_rows",[])
        if rows:
            sectors=["All sectors"]+sorted({str(r.get("sector") or "general") for r in rows}); chosen=st.selectbox("Audience",sectors)
            selected=rows if chosen=="All sectors" else [r for r in rows if (r.get("sector") or "general")==chosen]
            st.write(f"**{len(selected)}** recipients selected")
            if selected:
                preview=selected[0]; ps,pb=templates.render(preview)
                st.text_input("Campaign subject",ps,key="bulk_subject")
                st.text_area("Campaign message",pb,height=180,key="bulk_body")
                if st.button(f"Send to {len(selected)} customers",type="primary",use_container_width=True):
                    if not SENDER_EMAIL or not APP_PASSWORD: st.error("Configure sender credentials first.")
                    else:
                        progress=st.progress(0); sent_count=0; failed=0
                        def progress_cb(count,last): progress.progress(count/len(selected)); st.caption(f"Sending {count}/{len(selected)} · {last}")
                        for row in selected:
                            contact=db.get_contacts(); matches=[c for c in contact if c["email"].lower()==str(row["email"]).lower()]
                            if not matches:
                                db.upsert_contacts([row]); matches=[c for c in db.get_contacts() if c["email"].lower()==str(row["email"]).lower()]
                            if matches and send_one(matches[0],st.session_state["bulk_subject"],st.session_state["bulk_body"]): sent_count+=1
                            else: failed+=1
                            progress.progress((sent_count+failed)/len(selected))
                        st.success(f"Campaign finished — {sent_count} sent, {failed} failed.")
        st.markdown('</div>',unsafe_allow_html=True)

# ------------------------------ Customers ----------------------------------
else:
    st.markdown('<div class="page-title">Customers</div>',unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage contacts and keep a downloadable history of every interaction.</div>',unsafe_allow_html=True)
    add, imp = st.tabs(["Add customer","Import CSV"])
    with add:
        with st.form("add_customer"):
            n=st.text_input("Name"); e=st.text_input("Email"); co=st.text_input("Company"); se=st.text_input("Sector",placeholder="Optional — classified automatically if blank")
            if st.form_submit_button("Add customer",type="primary"):
                sector=se.strip() or classifier.classify(co); inserted,skipped=db.upsert_contacts([{"name":n,"email":e,"company":co,"sector":sector}]); st.success("Customer added." if inserted else "Customer already exists or email is invalid.")
    with imp:
        uploaded=st.file_uploader("Upload customer CSV/Excel",type=["csv","xlsx","xls"],key="customer_import")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded); df.columns=[str(c).strip().lower() for c in df.columns]
            if "sector" not in df.columns: df["sector"]=df["company"].apply(classifier.classify)
            else: df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
            edited=st.data_editor(df,num_rows="dynamic",use_container_width=True)
            if st.button("Import customers",type="primary"): inserted,skipped=db.upsert_contacts(edited.to_dict("records")); st.success(f"Imported {inserted}; skipped {skipped}.")
    customers=db.get_contacts()
    st.markdown('<div class="section-title">Customer list</div>',unsafe_allow_html=True)
    if customers:
        cdf=pd.DataFrame(customers); st.dataframe(cdf[["name","email","company","sector","status"]],use_container_width=True,hide_index=True)
        full=db.get_customer_history(); st.download_button("Download customer history",pd.DataFrame(full).to_csv(index=False).encode(),"outreach-customer-history.csv","text/csv",type="secondary")
    else: st.info("No customers yet.")

# Keep scheduled delivery active whenever the app receives a request.
if SENDER_EMAIL and APP_PASSWORD:
    try: sender.send_due_scheduled(SENDER_EMAIL,APP_PASSWORD)
    except Exception: pass
