"""Outreach UI: simple login + focused SaaS workspace."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import classifier
import db
import sender
import templates

IST = ZoneInfo("Asia/Kolkata")


def load_secrets():
    try:
        for key, value in st.secrets.items():
            os.environ.setdefault(key, str(value))
    except Exception:
        pass


def configure():
    load_secrets()
    st.set_page_config(page_title="Outreach", page_icon="✉", layout="wide", initial_sidebar_state="expanded")
    st.markdown("""
    <style>
      :root{--ink:#222235;--muted:#858696;--line:#e8e7ef;--purple:#7867e8;--green:#2eaf86;--red:#e76b78;--blue:#5d8eea}
      .stApp{background:linear-gradient(180deg,#fbfbfd 0%,#f7f7fb 100%);color:var(--ink)}
      [data-testid="stHeader"]{background:transparent}
      [data-testid="stSidebar"]{background:rgba(255,255,255,.96);border-right:1px solid var(--line)}
      [data-testid="stSidebar"]>div:first-child{padding:18px 14px}
      .brand{display:flex;align-items:center;gap:10px;height:55px;padding:0 9px;border-bottom:1px solid #efedf4;margin-bottom:20px}
      .logo{width:35px;height:35px;border-radius:10px;background:linear-gradient(135deg,var(--purple),#9b8cf4);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:850;font-size:19px;box-shadow:0 7px 18px rgba(120,103,232,.23)}
      .brand-name{font-size:20px;font-weight:820;letter-spacing:-.035em}.nav-caption{font-size:10px;text-transform:uppercase;letter-spacing:.11em;color:#a2a2b1;font-weight:800;padding:0 9px 8px}
      .page-title{font-size:32px;font-weight:850;letter-spacing:-.045em;line-height:1.05}.page-subtitle{font-size:13px;color:var(--muted);margin-top:6px}
      .metric{background:#fff;border:1px solid var(--line);border-radius:18px;padding:19px 20px;min-height:112px;box-shadow:0 8px 24px rgba(45,40,88,.045);position:relative;overflow:hidden}.metric:after{content:"";position:absolute;right:-25px;top:-25px;width:80px;height:80px;border-radius:50%;background:rgba(120,103,232,.08)}.metric-label{font-size:12px;color:#77788a;font-weight:760}.metric-value{font-size:31px;font-weight:850;letter-spacing:-.045em;margin-top:9px}.metric-note{font-size:11px;color:#999aaa;margin-top:3px}
      .card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:19px;box-shadow:0 8px 24px rgba(45,40,88,.035)}.section-title{font-size:16px;font-weight:800;margin:25px 0 10px}.section-sub{font-size:12px;color:#8c8d9e;margin:-3px 0 10px}.badge{display:inline-flex;padding:5px 9px;border-radius:999px;background:#eeeafd;color:#6653d7;font-size:11px;font-weight:760}.quick{background:#fff;border:1px solid var(--line);border-radius:15px;padding:15px 16px;box-shadow:0 7px 20px rgba(45,40,88,.035)}.small{font-size:12px;color:#858696}
      .login-wrap{max-width:420px;margin:12vh auto 0}.login-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:36px;box-shadow:0 22px 50px rgba(45,40,88,.08)}.login-logo{width:52px;height:52px;border-radius:15px;background:linear-gradient(135deg,var(--purple),#9b8cf4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:27px;font-weight:850;box-shadow:0 12px 24px rgba(120,103,232,.22)}.login-title{font-size:29px;font-weight:850;letter-spacing:-.045em;margin:22px 0 6px}.login-sub{font-size:13px;color:#858696;line-height:1.6;margin-bottom:22px}
      .stButton>button{border-radius:12px;min-height:42px;font-weight:780}.stButton>button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:#7159e6!important;background-color:#7159e6!important;border:1px solid #654bdc!important;color:#fff!important;box-shadow:0 9px 18px rgba(113,89,230,.22)!important;opacity:1!important}.stButton>button[kind="primary"] p,button[data-testid="stBaseButton-primary"] p{color:#fff!important}
      .stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{border-radius:12px!important;border-color:#e2e0e9!important}[data-testid="stTabs"] button{font-weight:760;color:#7f8091}[data-testid="stTabs"] button[aria-selected="true"]{color:#6753da}
    </style>
    """, unsafe_allow_html=True)


def live_clock():
    components.html("""
    <div style="font-family:Inter,system-ui,sans-serif;background:#fff;border:1px solid #e8e7ef;border-radius:999px;padding:8px 12px;color:#6f7080;font-size:12px;display:inline-flex;align-items:center;gap:7px;white-space:nowrap;box-shadow:0 5px 16px rgba(45,40,88,.04)"><span style="width:7px;height:7px;border-radius:50%;background:#2eaf86;display:inline-block"></span><span>IST · </span><span id="clock"></span></div>
    <script>function tick(){document.getElementById('clock').textContent=new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}).format(new Date())}tick();setInterval(tick,1000)</script>
    """, height=42, scrolling=False)


def credentials():
    return os.getenv("OUTREACH_LOGIN_EMAIL", "admin@outreach.local"), os.getenv("OUTREACH_LOGIN_PASSWORD", "Outreach@123")


def login():
    if st.session_state.get("authenticated"):
        return True
    st.markdown('<div class="login-wrap"><div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">O</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Sign in to Outreach</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-sub">Access your email outreach workspace, customers and campaign history.</div>', unsafe_allow_html=True)
    email = st.text_input("Email", placeholder="you@company.com")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    if st.button("Sign in", type="primary", use_container_width=True):
        expected_email, expected_password = credentials()
        if email.strip().lower() == expected_email.lower() and password == expected_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect email or password.")
    st.caption("Prototype credentials can be changed in Streamlit Secrets.")
    st.markdown('</div></div>', unsafe_allow_html=True)
    return False


def db_ready():
    try:
        db.init_db(); return True
    except Exception:
        return False


def metrics():
    try: return db.get_metrics()
    except Exception: return {"sent":0,"bounced":0,"replied":0,"daily":[]}


def customers():
    try: return db.get_contacts()
    except Exception: return []


def history():
    try:
        conn=db.get_conn();cur=conn.cursor();cur.execute("""SELECT e.id,e.contact_id,e.event_type,e.detail,e.subject,e.timestamp,c.name,c.email,c.company,c.sector FROM events e JOIN contacts c ON c.id=e.contact_id WHERE e.event_type IN ('sent','bounced','replied') ORDER BY e.timestamp DESC""")
        rows=[dict(r) for r in cur.fetchall()];cur.close();conn.close();return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()


def rel_time(value):
    try:
        dt=pd.to_datetime(value,utc=True).to_pydatetime();sec=max(0,int((datetime.now(timezone.utc)-dt).total_seconds()))
        if sec<60:return "just now"
        mins=sec//60
        if mins<60:return f"{mins}m ago"
        hrs=mins//60
        if hrs<24:return f"{hrs}h ago"
        days=hrs//24
        if days<7:return f"{days}d ago"
        return dt.astimezone(IST).strftime("%d %b %Y")
    except Exception:return ""


def header(title, subtitle):
    left,right=st.columns([5,2],vertical_alignment="top")
    with left: st.markdown(f'<div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>',unsafe_allow_html=True)
    with right: live_clock()


def activity_chart(daily, days):
    if not daily:return None
    raw=pd.DataFrame(daily);raw["date"]=pd.to_datetime(raw["d"]).dt.normalize();end=pd.Timestamp(datetime.now(IST).date());start=end-pd.Timedelta(days=days-1);idx=pd.date_range(start,end,freq="D")
    s=raw.pivot_table(index="date",columns="event_type",values="c",aggfunc="sum",fill_value=0).reindex(idx,fill_value=0)
    for k in ["sent","bounced","replied"]:
        if k not in s.columns:s[k]=0
    chart_df=s[["sent","bounced","replied"]].rename(columns={"sent":"Sent","bounced":"Bounce","replied":"Unique replies"}).reset_index(names="Date");long=chart_df.melt("Date",var_name="Status",value_name="Count")
    hover=alt.selection_point(on="pointerover",nearest=True,fields=["Date"],empty=False)
    base=alt.Chart(long).encode(x=alt.X("Date:T",title=None,axis=alt.Axis(format="%d %b",tickCount=min(9,days),grid=False,labelColor="#8b8c9d")),y=alt.Y("Count:Q",title=None,scale=alt.Scale(zero=True,nice=True),axis=alt.Axis(gridColor="#eeeaf3",domain=False,labelColor="#8b8c9d")),color=alt.Color("Status:N",title=None,scale=alt.Scale(domain=["Sent","Bounce","Unique replies"],range=["#7867e8","#e76b78","#5d8eea"])),tooltip=[alt.Tooltip("Date:T",title="Date",format="%d %b %Y"),alt.Tooltip("Status:N",title="Type"),alt.Tooltip("Count:Q",title="Count")])
    return (base.mark_line(interpolate="monotone",strokeWidth=3)+base.mark_circle(size=58).encode(opacity=alt.condition(hover,alt.value(1),alt.value(.35)))+alt.Chart(long).mark_rule(color="#c9c6d6").encode(x="Date:T",opacity=alt.condition(hover,alt.value(.7),alt.value(0))).add_params(hover)).properties(height=330).configure_view(stroke=None).configure_legend(orient="top",labelColor="#676878")


def dashboard():
    header("Dashboard","Your outbound email activity at a glance.")
    m=metrics();a,b,c=st.columns(3)
    with a: st.markdown(f'<div class="metric"><div class="metric-label">Mail sent</div><div class="metric-value">{m["sent"]:,}</div><div class="metric-note">Successful outbound emails</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="metric"><div class="metric-label">Bounce</div><div class="metric-value">{m["bounced"]:,}</div><div class="metric-note">Delivery failures</div></div>',unsafe_allow_html=True)
    with c: st.markdown(f'<div class="metric"><div class="metric-label">Unique replies</div><div class="metric-value">{m["replied"]:,}</div><div class="metric-note">Customers who replied</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Email activity</div><div class="section-sub">Replies are counted once per customer.</div>',unsafe_allow_html=True)
    left,right=st.columns([4,1])
    with right: range_label=st.selectbox("Range",["7 days","30 days","90 days"],index=1)
    with left:
        chart=activity_chart(m.get("daily",[]),int(range_label.split()[0]))
        if chart: st.markdown('<div class="card">',unsafe_allow_html=True);st.altair_chart(chart,use_container_width=True);st.markdown('</div>',unsafe_allow_html=True)
        else: st.markdown('<div class="card"><b>Your email activity will appear here</b><div class="small">Send your first email to build the timeline.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Quick actions</div>',unsafe_allow_html=True)
    q1,q2,q3=st.columns(3)
    with q1: st.markdown('<div class="quick"><b>✉ Write an email</b><div class="small">Compose a personal message.</div></div>',unsafe_allow_html=True)
    with q2: st.markdown('<div class="quick"><b>↗ Send to many</b><div class="small">Launch a CSV campaign.</div></div>',unsafe_allow_html=True)
    with q3: st.markdown('<div class="quick"><b>＋ Add customer</b><div class="small">Create a customer manually.</div></div>',unsafe_allow_html=True)


def emails():
    header("Emails","Send, schedule and review every outbound email.")
    history_tab,compose_tab,bulk_tab=st.tabs(["History","Compose","Send to many"])
    with history_tab:
        h=history();sbox,pbox,statusbox,download=st.columns([2.5,1,1,.5])
        with sbox:q=st.text_input("Search",placeholder="Search name, company or sector",label_visibility="collapsed")
        with pbox:p=st.selectbox("Period",["Last 15 days","Last 30 days","All time"],label_visibility="collapsed")
        with statusbox:s=st.selectbox("Status",["All","Delivered","Bounced","Replied"],label_visibility="collapsed")
        with download:
            data=h.to_csv(index=False).encode() if not h.empty else b"";st.download_button("↓",data,"outreach-email-history.csv","text/csv",disabled=not bool(data),help="Download email history")
        f=h.copy()
        if not f.empty:
            f["dt"]=pd.to_datetime(f["timestamp"],utc=True,errors="coerce")
            if p!="All time":f=f[f["dt"]>=datetime.now(timezone.utc)-timedelta(days=15 if p=="Last 15 days" else 30)]
            if s!="All":f=f[f["event_type"]==("sent" if s=="Delivered" else s.lower())]
            if q:
                mask=pd.Series(False,index=f.index)
                for field in ["name","company","email","sector"]:mask|=f[field].fillna("").astype(str).str.contains(q,case=False,na=False)
                f=f[mask]
        st.markdown('<div class="card">',unsafe_allow_html=True)
        if f.empty: st.info("No outbound email history yet.")
        else:
            cols=st.columns([.45,1.55,1.55,2.3,1.2,1])
            for col,text in zip(cols,["#","NAME","COMPANY","EMAIL","SECTOR","SENT"]):col.markdown(f"**{text}**")
            for n,(_,r) in enumerate(f.sort_values("dt",ascending=False).iterrows(),1):
                cols=st.columns([.45,1.55,1.55,2.3,1.2,1]);cols[0].write(n);cols[1].write(r.get("name") or "—");cols[2].write(r.get("company") or "—");cols[3].write(r.get("email") or "—");cols[4].markdown(f'<span class="badge">{r.get("sector") or "General"}</span>',unsafe_allow_html=True);cols[5].write(rel_time(r.get("timestamp")))
        st.markdown('</div>',unsafe_allow_html=True)
        if st.button("Sync replies & bounces"):
            se=os.getenv("SENDER_EMAIL","");pw=os.getenv("SENDER_APP_PASSWORD","")
            if not se or not pw:st.warning("Configure sender credentials first.")
            else:
                try:r=sender.check_replies_and_bounces(se,pw);st.success(f"Synced {r['replies_found']} replies and {r['bounces_found']} bounces.");st.rerun()
                except Exception as exc:st.error(f"Sync failed: {exc}")
    with compose_tab:
        cs=customers();opts={f"{c['name']} · {c['email']}":c for c in cs}
        if not opts:st.info("Add a customer from Customers first.")
        else:
            customer=opts[st.selectbox("Customer",list(opts.keys()))];st.markdown(f'<span class="badge">{customer.get("sector") or "General"}</span>',unsafe_allow_html=True)
            mode=st.radio("Message",["Write manually","Use classified template"],horizontal=True)
            if mode=="Write manually":subject=st.text_input("Subject",placeholder="Write your subject");body=st.text_area("Message",height=240,placeholder="Write your email...")
            else:subject,body=templates.render(customer);st.text_input("Subject",subject,disabled=True);st.text_area("Message",body,height=240,disabled=True);st.caption(f"Using {customer.get('sector') or 'general'} sector template.")
            x,y=st.columns(2)
            with x:
                if st.button("Send now",type="primary",use_container_width=True):
                    se=os.getenv("SENDER_EMAIL","");pw=os.getenv("SENDER_APP_PASSWORD","")
                    if not se or not pw:st.error("Configure sender credentials first.")
                    elif not subject.strip() or not body.strip():st.warning("Add a subject and message first.")
                    else:
                        try:sender.send_one(se,pw,customer["email"],subject,body);db.log_event(customer["id"],"sent",subject=subject);st.success(f"Sent to {customer['email']}");st.rerun()
                        except Exception as exc:db.log_event(customer["id"],"bounced",str(exc),subject);st.error(str(exc))
            with y:
                if st.button("Schedule for later",use_container_width=True):st.session_state["schedule_open"]=True
            if st.session_state.get("schedule_open"):
                st.markdown('<div class="card">',unsafe_allow_html=True);st.markdown("**Schedule in India Standard Time**");d=st.date_input("Date",datetime.now(IST).date(),min_value=datetime.now(IST).date());t=st.time_input("Time (IST)",(datetime.now(IST)+timedelta(hours=1)).replace(second=0,microsecond=0).time())
                if st.button("Confirm schedule",type="primary"):
                    local=datetime.combine(d,t).replace(tzinfo=IST);db.schedule_email(customer["id"],subject,body,local.astimezone(timezone.utc).isoformat());st.session_state["schedule_open"]=False;st.success(f"Scheduled for {local.strftime('%d %b %Y · %I:%M %p')} IST");st.rerun()
                st.markdown('</div>',unsafe_allow_html=True)
    with bulk_tab:
        st.markdown('<div class="card"><b>Send many emails in one shot</b><div class="small">Upload → classify → edit → select audience → write → send.</div></div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("Upload CSV or Excel",type=["csv","xlsx","xls"],key="bulk_upload")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded);df.columns=[str(c).strip().lower() for c in df.columns];missing=[x for x in ["name","email","company"] if x not in df.columns]
            if missing:st.error("Missing required columns: "+", ".join(missing))
            else:
                if "sector" not in df.columns:df["sector"]=df["company"].apply(classifier.classify)
                else:df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
                edited=st.data_editor(df,num_rows="dynamic",use_container_width=True,key="bulk_editor");st.session_state["bulk_rows"]=edited.to_dict("records")
        rows=st.session_state.get("bulk_rows",[])
        if rows:
            sectors=["All sectors"]+sorted({str(r.get("sector") or "general") for r in rows});chosen=st.selectbox("Audience",sectors);selected=rows if chosen=="All sectors" else [r for r in rows if (r.get("sector") or "general")==chosen];st.write(f"{len(selected)} recipient(s) selected")
            if selected:
                subject,body=templates.render(selected[0]);subject=st.text_input("Campaign subject",subject,key="bulk_subject");body=st.text_area("Campaign message",body,height=210,key="bulk_body");delay=st.slider("Delay between emails (seconds)",5,60,15,5)
                if st.button(f"Send to {len(selected)} customers",type="primary",use_container_width=True):
                    se=os.getenv("SENDER_EMAIL","");pw=os.getenv("SENDER_APP_PASSWORD","")
                    if not se or not pw:st.error("Configure sender credentials first.")
                    else:
                        known={c["email"].lower():c for c in customers()};prepared=[]
                        for row in selected:
                            email=str(row.get("email") or "").strip().lower()
                            if not email:continue
                            if email not in known:db.upsert_contacts([row]);known={c["email"].lower():c for c in customers()}
                            if email in known:prepared.append(known[email])
                        progress=st.progress(0);box=st.empty();sent_count=failed=0
                        for i,cust in enumerate(prepared,1):
                            box.info(f"Sending {i}/{len(prepared)} · {cust['email']}")
                            try:sender.send_one(se,pw,cust["email"],subject,body);db.log_event(cust["id"],"sent",subject=subject);sent_count+=1
                            except Exception as exc:db.log_event(cust["id"],"bounced",str(exc),subject);failed+=1
                            progress.progress(i/len(prepared))
                            if i<len(prepared):time.sleep(delay)
                        box.success(f"Campaign complete · {sent_count} sent · {failed} failed")


def customers_page():
    header("Customers","Manage customers and their complete communication history.")
    add_tab,list_tab=st.tabs(["Add customer","Customer list"])
    with add_tab:
        st.markdown('<div class="card">',unsafe_allow_html=True);st.markdown("### Add a customer");a,b=st.columns(2)
        with a:name=st.text_input("Name")
        with b:email=st.text_input("Email")
        a,b=st.columns(2)
        with a:company=st.text_input("Company")
        with b:sector=st.selectbox("Sector",["general","healthcare","fintech","saas_tech","manufacturing","retail_ecom"])
        if st.button("Save customer",type="primary"):
            if not name.strip() or not email.strip() or not company.strip():st.warning("Name, email and company are required.")
            else:
                inserted,_=db.upsert_contacts([{"name":name,"email":email,"company":company,"sector":sector}]);st.success("Customer added.") if inserted else st.info("Customer already exists or email is invalid.")
        st.markdown('</div>',unsafe_allow_html=True)
        st.markdown('<div class="section-title">Import customers</div>',unsafe_allow_html=True)
        uploaded=st.file_uploader("CSV or Excel · required: name, email, company · optional: sector",type=["csv","xlsx","xls"],key="customer_upload")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded);df.columns=[str(c).strip().lower() for c in df.columns];missing=[x for x in ["name","email","company"] if x not in df.columns]
            if missing:st.error("Missing required columns: "+", ".join(missing))
            else:
                if "sector" not in df.columns:df["sector"]=df["company"].apply(classifier.classify)
                else:df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
                edited=st.data_editor(df,num_rows="dynamic",use_container_width=True,key="customer_editor")
                if st.button("Import customers",type="primary"):
                    inserted,skipped=db.upsert_contacts(edited.to_dict("records"));st.success(f"Imported {inserted} customers · skipped {skipped} duplicates/invalid rows.")
    with list_tab:
        cs=customers()
        if not cs:st.info("No customers yet.")
        else:
            q=st.text_input("Search customers",placeholder="Search name, email, company or sector");filtered=[c for c in cs if not q or q.lower() in f"{c.get('name','')} {c.get('email','')} {c.get('company','')} {c.get('sector','')}".lower()]
            all_hist=pd.DataFrame(db.get_customer_history());all_csv=all_hist.to_csv(index=False).encode() if not all_hist.empty else b"";l,r=st.columns([4,1])
            with l:st.markdown(f'<div class="section-title" style="margin-top:8px">{len(filtered)} customer(s)</div>',unsafe_allow_html=True)
            with r:st.download_button("Download all history",all_csv,"outreach-customer-history.csv","text/csv",disabled=not bool(all_csv),use_container_width=True)
            for c in filtered:
                st.markdown('<div class="card" style="margin-bottom:11px">',unsafe_allow_html=True);left,right=st.columns([3.8,1.2])
                with left:st.markdown(f'<b>{c.get("name","")}</b> <span class="badge">{c.get("sector") or "General"}</span>',unsafe_allow_html=True);st.markdown(f'<div class="small">{c.get("email","")} · {c.get("company","")}</div>',unsafe_allow_html=True)
                ch=pd.DataFrame(db.get_customer_history(c["id"]));csv=ch.to_csv(index=False).encode() if not ch.empty else b""
                with right:st.download_button("Download history",csv,f"{c.get('name','customer')}-history.csv","text/csv",disabled=not bool(csv),use_container_width=True,key=f"hist_{c['id']}")
                with st.expander("View customer history"):
                    if ch.empty:st.caption("No communication history yet.")
                    else:
                        view=ch[[x for x in ["event_type","sector","subject","detail","timestamp"] if x in ch.columns]].copy();view["timestamp"]=pd.to_datetime(view["timestamp"],utc=True,errors="coerce").dt.tz_convert("Asia/Kolkata").dt.strftime("%d %b %Y · %I:%M %p IST");view=view.rename(columns={"event_type":"Status","sector":"Sector","subject":"Subject","detail":"Details","timestamp":"Time"});st.dataframe(view,use_container_width=True,hide_index=True)
                st.markdown('</div>',unsafe_allow_html=True)


def main():
    configure()
    if not login(): return
    if not db_ready(): st.warning("Customer data is temporarily unavailable. The interface is still available.")
    with st.sidebar:
        st.markdown('<div class="brand"><div class="logo">O</div><div class="brand-name">Outreach</div></div>',unsafe_allow_html=True)
        st.markdown('<div class="nav-caption">Workspace</div>',unsafe_allow_html=True)
        page=st.radio("Navigation",["Dashboard","Emails","Customers"],label_visibility="collapsed")
        st.divider();st.markdown('<div class="small">Sending from</div>',unsafe_allow_html=True);st.caption(os.getenv("SENDER_EMAIL","Not configured"));st.markdown('<div class="small">Timezone</div>',unsafe_allow_html=True);st.caption("India Standard Time (IST)")
        if st.button("Log out",use_container_width=True):st.session_state["authenticated"]=False;st.rerun()
    if page=="Dashboard":dashboard()
    elif page=="Emails":emails()
    else:customers_page()


if __name__ == "__main__":
    main()
