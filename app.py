"""Outreach - polished email operations workspace."""

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
NOW_IST = datetime.now(IST)

# -----------------------------------------------------------------------------
# Visual language inspired by the supplied reference: airy canvas, soft
# lavender/blue gradient accents, rounded cards, subtle shadows and strong
# typography. The product remains intentionally focused on three areas.
st.markdown("""
<style>
:root {
  --ink:#202033;
  --muted:#7a7b8d;
  --line:#e9e8f1;
  --surface:#ffffff;
  --canvas:#f7f7fb;
  --purple:#7867e8;
  --purple-dark:#6552df;
  --purple-soft:#eeeaff;
  --blue:#5b8def;
  --green:#31b68a;
  --red:#ef6b7a;
}
.stApp {
  background:
    radial-gradient(circle at 12% 0%, rgba(245,220,202,.42), transparent 24%),
    radial-gradient(circle at 85% 2%, rgba(213,228,255,.46), transparent 25%),
    linear-gradient(180deg,#fbfbfd 0%,var(--canvas) 100%);
  color:var(--ink);
}
[data-testid="stHeader"] { background:rgba(255,255,255,0); }
[data-testid="stSidebar"] {
  background:rgba(255,255,255,.92);
  border-right:1px solid rgba(231,230,240,.9);
  box-shadow:6px 0 24px rgba(50,45,90,.04);
}
[data-testid="stSidebar"] > div:first-child { padding:24px 14px; }
.brand { display:flex; align-items:center; gap:10px; font-size:1.18rem; font-weight:800; color:var(--ink); margin:2px 10px 28px; }
.brand-mark { width:32px;height:32px;border-radius:10px;background:linear-gradient(135deg,var(--purple),#9c8cf5);color:#fff;display:inline-flex;align-items:center;justify-content:center;font-weight:800;box-shadow:0 8px 22px rgba(120,103,232,.28); }
.nav-caption { color:#a0a0af; font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; margin:0 10px 8px; }
.page-shell { padding-top:4px; }
.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.page-title { font-size:2.15rem; line-height:1.08; font-weight:820; letter-spacing:-.045em; color:var(--ink); }
.page-subtitle { color:var(--muted); font-size:.93rem; margin:6px 0 24px; }
.ist-pill { display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.88);border:1px solid var(--line);border-radius:999px;padding:7px 12px;font-size:.75rem;color:#696a7a;box-shadow:0 6px 18px rgba(60,55,100,.05); }
.dot { width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 0 4px rgba(49,182,138,.12); }
.card { background:rgba(255,255,255,.92); border:1px solid var(--line); border-radius:18px; padding:20px; box-shadow:0 8px 28px rgba(58,50,108,.045); }
.hero-card { background:linear-gradient(135deg,rgba(120,103,232,.12),rgba(91,141,239,.08) 58%,rgba(255,255,255,.9)); border:1px solid #e7e3fb; border-radius:22px; padding:22px; box-shadow:0 16px 38px rgba(78,66,144,.08); }
.metric { background:rgba(255,255,255,.96); border:1px solid var(--line); border-radius:18px; padding:19px 20px; min-height:118px; box-shadow:0 8px 24px rgba(50,45,90,.045); position:relative; overflow:hidden; }
.metric:after { content:""; position:absolute; right:-26px; top:-26px; width:84px; height:84px; border-radius:50%; background:linear-gradient(135deg,rgba(120,103,232,.13),rgba(120,103,232,0)); }
.metric-label { color:#78798a; font-size:.78rem; font-weight:700; }
.metric-value { font-size:2rem; font-weight:820; letter-spacing:-.04em; margin-top:8px; color:var(--ink); }
.metric-note { font-size:.74rem; color:#9a9baa; margin-top:4px; }
.section-title { font-size:1.02rem; font-weight:780; margin:26px 0 11px; color:var(--ink); }
.section-subtitle { color:#8c8d9d; font-size:.78rem; margin-top:-6px; margin-bottom:10px; }
.status-delivered { color:#159a70; font-weight:750; }
.status-bounced { color:#df5466; font-weight:750; }
.status-replied { color:#7358df; font-weight:750; }
.badge { display:inline-flex;align-items:center;padding:5px 9px;border-radius:999px;font-size:.7rem;font-weight:700;background:var(--purple-soft);color:var(--purple-dark); }
.quick-action { background:#fff;border:1px solid var(--line);border-radius:16px;padding:15px 16px;box-shadow:0 7px 22px rgba(50,45,90,.04); }
.small-muted { color:#858696; font-size:.79rem; }
.divider { height:1px;background:#efedf4;margin:14px 0; }
.stButton > button { border-radius:12px; font-weight:700; min-height:42px; }
button[kind="primary"] { background:linear-gradient(135deg,var(--purple),#8a79ee) !important; border-color:var(--purple) !important; box-shadow:0 8px 18px rgba(120,103,232,.20); }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div { border-radius:12px !important; border-color:#e4e2ec !important; }
[data-testid="stTabs"] { margin-top:4px; }
[data-testid="stTabs"] button { font-weight:720; color:#7c7d8e; }
[data-testid="stTabs"] button[aria-selected="true"] { color:var(--purple-dark); }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Scheduled mail is processed whenever the deployed app is active.
if SENDER_EMAIL and APP_PASSWORD:
    try:
        sender.send_due_scheduled(SENDER_EMAIL, APP_PASSWORD)
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Navigation: only the three product areas requested.
with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">O</span>Outreach</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-caption">Workspace</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["Dashboard", "Emails", "Customers"], label_visibility="collapsed")
    st.divider()
    st.caption("Sending from")
    st.write(SENDER_EMAIL or "Not configured")
    st.caption("Timezone")
    st.write("India Standard Time (IST)")


def history_df():
    try:
        conn = db.get_conn(); cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.contact_id, e.event_type, e.detail, e.subject, e.timestamp,
                   c.name, c.email, c.company, c.sector
            FROM events e
            JOIN contacts c ON c.id=e.contact_id
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
        return dt.astimezone(IST).strftime("%d %b %Y")
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
        st.error(f"Could not send to {contact['email']}: {exc}")
        return False


def customer_options():
    return {f"{c['name']} · {c['email']}": c for c in db.get_contacts()}


def activity_chart(metrics_df, days):
    if metrics_df.empty:
        return None
    raw = metrics_df.copy()
    raw["date"] = pd.to_datetime(raw["d"]).dt.normalize()
    end = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None).normalize()
    start = end - pd.Timedelta(days=days-1)
    date_index = pd.date_range(start, end, freq="D")
    series = raw.pivot_table(index="date", columns="event_type", values="c", aggfunc="sum", fill_value=0).reindex(date_index, fill_value=0)
    for key in ["sent", "bounced", "replied"]:
        if key not in series.columns: series[key] = 0
    chart_df = series[["sent","bounced","replied"]].rename(columns={"sent":"Sent","bounced":"Bounce","replied":"Reply"}).reset_index(names="Date")
    long = chart_df.melt("Date", var_name="Status", value_name="Emails")
    hover = alt.selection_point(on="pointerover", nearest=True, fields=["Date"], empty=False)
    base = alt.Chart(long).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%d %b", tickCount=min(9, days), labelColor="#8a8b9b", grid=False)),
        y=alt.Y("Emails:Q", title=None, scale=alt.Scale(zero=True, nice=True), axis=alt.Axis(labelColor="#8a8b9b", gridColor="#efedf4", domain=False)),
        color=alt.Color("Status:N", title=None, scale=alt.Scale(domain=["Sent","Bounce","Reply"], range=["#7b68e8","#ef6b7a","#5d8eea"])),
        tooltip=[alt.Tooltip("Date:T", title="Date", format="%d %b %Y"), alt.Tooltip("Status:N", title="Type"), alt.Tooltip("Emails:Q", title="Emails")],
    )
    lines = base.mark_line(interpolate="monotone", strokeWidth=2.8)
    points = base.mark_circle(size=64).encode(opacity=alt.condition(hover, alt.value(1), alt.value(.35)))
    rule = alt.Chart(long).mark_rule(color="#c9c6d6").encode(x="Date:T", opacity=alt.condition(hover, alt.value(.7), alt.value(0))).add_params(hover)
    return (lines + points + rule).properties(height=340).configure_view(stroke=None).configure_legend(orient="top", labelColor="#676878")


# -----------------------------------------------------------------------------
# Dashboard
if page == "Dashboard":
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.markdown('<div class="topbar"><div><div class="page-title">Good afternoon</div><div class="page-subtitle">Your outbound email performance, at a glance.</div></div><div class="ist-pill"><span class="dot"></span> IST · '+NOW_IST.strftime('%d %b %Y · %I:%M %p')+'</div></div>', unsafe_allow_html=True)

    metrics = db.get_metrics()
    a,b,c = st.columns(3)
    with a:
        st.markdown(f'<div class="metric"><div class="metric-label">Mail sent</div><div class="metric-value">{metrics["sent"]:,}</div><div class="metric-note">Successful outbound emails</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="metric"><div class="metric-label">Bounce</div><div class="metric-value">{metrics["bounced"]:,}</div><div class="metric-note">Delivery failures</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="metric"><div class="metric-label">Reply</div><div class="metric-value">{metrics["replied"]:,}</div><div class="metric-note">Replies detected</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Email activity</div><div class="section-subtitle">Hover any point to inspect the exact count for that day.</div>', unsafe_allow_html=True)
    graph_left, graph_right = st.columns([4,1])
    with graph_right:
        range_label = st.selectbox("Time range", ["7 days","30 days","90 days"], index=1)
        days = int(range_label.split()[0])
    if metrics.get("daily"):
        daily = pd.DataFrame(metrics["daily"])
        graph = activity_chart(daily, days)
        if graph is not None:
            with graph_left:
                st.markdown('<div class="hero-card">', unsafe_allow_html=True)
                st.altair_chart(graph, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        with graph_left:
            st.markdown('<div class="hero-card"><h4 style="margin:0;color:#27263a">Your activity graph will appear here</h4><p style="color:#898999;margin-bottom:0">Send your first email to start building the timeline.</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Quick actions</div>', unsafe_allow_html=True)
    q1,q2,q3 = st.columns(3)
    with q1:
        st.markdown('<div class="quick-action"><b>✉ Write an email</b><div class="small-muted">Compose a personal message.</div></div>', unsafe_allow_html=True)
    with q2:
        st.markdown('<div class="quick-action"><b>⇢ Send to many</b><div class="small-muted">Launch a CSV campaign.</div></div>', unsafe_allow_html=True)
    with q3:
        st.markdown('<div class="quick-action"><b>＋ Add customer</b><div class="small-muted">Create a contact manually.</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Emails
elif page == "Emails":
    st.markdown('<div class="topbar"><div><div class="page-title">Emails</div><div class="page-subtitle">Send, schedule and review every outbound email.</div></div><div class="ist-pill"><span class="dot"></span> India · IST</div></div>', unsafe_allow_html=True)
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
        st.markdown('<div class="card">',unsafe_allow_html=True)
        if f.empty:
            st.info("No outbound email history yet.")
        else:
            head=st.columns([2.4,1,3.6,.85]); [head[i].markdown(x) for i,x in enumerate(["**TO**","**STATUS**","**SUBJECT**","**SENT**"])]
            for _,r in f.sort_values("dt",ascending=False).iterrows():
                cols=st.columns([2.4,1,3.6,.85]); event=str(r["event_type"]); label="Delivered" if event=="sent" else event.capitalize()
                cols[0].write(r.get("email","")); cols[1].markdown(f'<span class="status-{label.lower()}">{label}</span>',unsafe_allow_html=True); cols[2].write(r.get("subject") or r.get("detail") or "Outbound email"); cols[3].write(relative_time(r.get("timestamp")))
        st.markdown('</div>',unsafe_allow_html=True)
        if st.button("Sync replies & bounces"):
            if SENDER_EMAIL and APP_PASSWORD:
                result=sender.check_replies_and_bounces(SENDER_EMAIL,APP_PASSWORD); st.success(f"Synced {result['replies_found']} replies and {result['bounces_found']} bounces."); st.rerun()
            else: st.warning("Configure sender credentials first.")

    with tab_compose:
        contacts=customer_options()
        if not contacts:
            st.info("Add a customer from Customers first.")
        else:
            selected=st.selectbox("Customer",list(contacts.keys())); contact=contacts[selected]
            mode=st.radio("Message",["Write manually","Use classified template"],horizontal=True)
            if mode=="Write manually":
                subject=st.text_input("Subject",placeholder="Write your subject")
                body=st.text_area("Message",height=250,placeholder="Write your email...")
            else:
                subject,body=templates.render(contact)
                st.text_input("Subject",subject,disabled=True)
                st.text_area("Message",body,height=250,disabled=True)
                st.caption(f"Using {contact.get('sector') or 'general'} sector template.")
            x,y = st.columns(2)
            with x:
                if st.button("Send now",type="primary",use_container_width=True):
                    if not subject.strip() or not body.strip(): st.warning("Add a subject and message first.")
                    elif send_one(contact,subject,body): st.success(f"Sent to {contact['email']}."); st.rerun()
            with y:
                if st.button("Schedule for later",use_container_width=True): st.session_state["schedule_open"]=True
            if st.session_state.get("schedule_open"):
                st.markdown('<div class="card" style="margin-top:14px">',unsafe_allow_html=True)
                st.markdown("**Schedule in India Standard Time**")
                d=st.date_input("Date",NOW_IST.date(),min_value=NOW_IST.date())
                t=st.time_input("Time (IST)",(NOW_IST+timedelta(hours=1)).replace(second=0,microsecond=0).time())
                if st.button("Confirm schedule",type="primary"):
                    local=datetime.combine(d,t).replace(tzinfo=IST)
                    db.schedule_email(contact["id"],subject,body,local.astimezone(timezone.utc).isoformat())
                    st.session_state["schedule_open"]=False
                    st.success(f"Scheduled for {local.strftime('%d %b %Y · %I:%M %p')} IST.")
                    st.rerun()
                st.markdown('</div>',unsafe_allow_html=True)
            scheduled=db.get_scheduled_emails("scheduled")
            if scheduled:
                st.markdown('<div class="section-title">Upcoming</div>',unsafe_allow_html=True)
                for item in scheduled:
                    when=pd.to_datetime(item["scheduled_for"],utc=True).tz_convert("Asia/Kolkata").strftime("%d %b %Y · %I:%M %p")
                    st.markdown(f'<div class="card" style="margin-bottom:8px"><b>{item["name"]}</b> · {item["email"]}<br><span class="small-muted">{when} IST · {item["subject"]}</span></div>',unsafe_allow_html=True)

    with tab_bulk:
        st.markdown('<div class="hero-card">',unsafe_allow_html=True)
        st.markdown("### Send many emails in one shot")
        st.markdown('<div class="small-muted">Upload a list → classify it → edit the audience → write one campaign message → send the batch.</div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("Upload CSV or Excel",type=["csv","xlsx","xls"],key="bulk_upload")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns=[str(c).strip().lower() for c in df.columns]
            missing=[x for x in ["name","email","company"] if x not in df.columns]
            if missing:
                st.error("Missing required columns: "+", ".join(missing))
            else:
                if "sector" not in df.columns:
                    df["sector"]=df["company"].apply(classifier.classify)
                else:
                    df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
                edited=st.data_editor(df,num_rows="dynamic",use_container_width=True,key="bulk_editor")
                st.session_state["bulk_rows"]=edited.to_dict("records")
        rows=st.session_state.get("bulk_rows",[])
        if rows:
            sectors=["All sectors"]+sorted({str(r.get("sector") or "general") for r in rows})
            chosen=st.selectbox("Audience",sectors)
            selected=rows if chosen=="All sectors" else [r for r in rows if (r.get("sector") or "general")==chosen]
            st.write(f"{len(selected)} recipient(s) selected")
            if selected:
                preview=selected[0]
                preview_subject,preview_body=templates.render(preview)
                subject=st.text_input("Campaign subject",preview_subject,key="bulk_subject")
                body=st.text_area("Campaign message",preview_body,height=210,key="bulk_body")
                delay=st.slider("Delay between emails (seconds)",min_value=5,max_value=60,value=15,step=5)
                st.caption("Emails are sent sequentially through the connected sender to keep the current prototype conservative.")
                if st.button(f"Send to {len(selected)} customers",type="primary",use_container_width=True):
                    if not SENDER_EMAIL or not APP_PASSWORD:
                        st.error("Configure sender credentials first.")
                    else:
                        prepared=[]
                        all_contacts=db.get_contacts()
                        by_email={c["email"].lower():c for c in all_contacts}
                        for row in selected:
                            email_addr=str(row.get("email") or "").strip().lower()
                            if not email_addr: continue
                            contact=by_email.get(email_addr)
                            if not contact:
                                db.upsert_contacts([row])
                                refreshed=db.get_contacts()
                                by_email={c["email"].lower():c for c in refreshed}
                                contact=by_email.get(email_addr)
                            if contact: prepared.append(contact)
                        progress=st.progress(0); status_box=st.empty(); sent_count=0; failed=0
                        for idx,contact in enumerate(prepared,1):
                            status_box.info(f"Sending {idx}/{len(prepared)} · {contact['email']}")
                            if send_one(contact,subject,body): sent_count+=1
                            else: failed+=1
                            progress.progress(idx/len(prepared))
                            if idx < len(prepared):
                                import time; time.sleep(delay)
                        status_box.success(f"Campaign complete · {sent_count} sent · {failed} failed")
        st.markdown('</div>',unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Customers
else:
    st.markdown('<div class="topbar"><div><div class="page-title">Customers</div><div class="page-subtitle">Your customer list and complete communication history.</div></div><div class="ist-pill"><span class="dot"></span> India Standard Time</div></div>',unsafe_allow_html=True)
    add_tab,list_tab = st.tabs(["Add customer","Customer list"])

    with add_tab:
        st.markdown('<div class="card">',unsafe_allow_html=True)
        st.markdown("### Add a customer")
        c1,c2=st.columns(2)
        with c1: name=st.text_input("Name")
        with c2: email_addr=st.text_input("Email")
        c3,c4=st.columns(2)
        with c3: company=st.text_input("Company")
        with c4: sector=st.selectbox("Sector",["general","healthcare","fintech","saas_tech","manufacturing","retail_ecom"])
        if st.button("Save customer",type="primary"):
            if not name.strip() or not email_addr.strip() or not company.strip():
                st.warning("Name, email and company are required.")
            else:
                inserted,skipped=db.upsert_contacts([{"name":name,"email":email_addr,"company":company,"sector":sector}])
                if inserted: st.success("Customer added.")
                else: st.info("That customer already exists or the email is invalid.")
        st.markdown('</div>',unsafe_allow_html=True)

        st.markdown('<div class="section-title">Import customers</div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("CSV or Excel · required: name, email, company · optional: sector",type=["csv","xlsx","xls"],key="customer_upload")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns=[str(c).strip().lower() for c in df.columns]
            missing=[x for x in ["name","email","company"] if x not in df.columns]
            if missing:
                st.error("Missing required columns: "+", ".join(missing))
            else:
                if "sector" not in df.columns: df["sector"]=df["company"].apply(classifier.classify)
                else: df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
                edited=st.data_editor(df,num_rows="dynamic",use_container_width=True,key="customer_editor")
                if st.button("Import customers",type="primary"):
                    inserted,skipped=db.upsert_contacts(edited.to_dict("records"))
                    st.success(f"Imported {inserted} customers · skipped {skipped} duplicates/invalid rows.")

    with list_tab:
        customers=db.get_contacts()
        if not customers:
            st.info("No customers yet.")
        else:
            search=st.text_input("Search customers",placeholder="Search name, email or company")
            filtered=customers
            if search:
                filtered=[c for c in customers if search.lower() in f"{c.get('name','')} {c.get('email','')} {c.get('company','')}".lower()]
            st.markdown(f'<div class="section-title">{len(filtered)} customer(s)</div>',unsafe_allow_html=True)
            for c in filtered:
                st.markdown('<div class="card" style="margin-bottom:10px">',unsafe_allow_html=True)
                left,right=st.columns([4,1])
                with left:
                    st.markdown(f"**{c.get('name','')}**  <span class='badge'>{c.get('sector') or 'general'}</span>",unsafe_allow_html=True)
                    st.markdown(f"<span class='small-muted'>{c.get('email','')} · {c.get('company','')}</span>",unsafe_allow_html=True)
                with right:
                    history=db.get_customer_history(c["id"])
                    history_df_export=pd.DataFrame(history)
                    csv=history_df_export.to_csv(index=False).encode("utf-8") if not history_df_export.empty else b""
                    st.download_button("Download history",csv,f"{c.get('name','customer')}-history.csv","text/csv",disabled=not bool(csv),key=f"download_{c['id']}")
                if history:
                    latest=history[0]
                    latest_label="Delivered" if latest.get("event_type")=="sent" else str(latest.get("event_type") or "activity").capitalize()
                    st.markdown(f"<div class='small-muted'>Latest activity: {latest_label} · {relative_time(latest.get('timestamp'))} · {latest.get('subject') or latest.get('detail') or 'No subject'}</div>",unsafe_allow_html=True)
                else:
                    st.markdown("<div class='small-muted'>No email activity yet.</div>",unsafe_allow_html=True)
                st.markdown('</div>',unsafe_allow_html=True)
