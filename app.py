"""Outreach - focused outbound email workspace."""
from dotenv import load_dotenv
load_dotenv()

import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
IST=ZoneInfo("Asia/Kolkata");SENDER_EMAIL=os.getenv("SENDER_EMAIL","");APP_PASSWORD=os.getenv("SENDER_APP_PASSWORD","")

st.markdown("""
<style>
:root{--ink:#202033;--muted:#7d7e8f;--line:#e9e7f0;--purple:#7867e8;--soft:#f7f7fb;--green:#2eaf86;--red:#e76b78;--blue:#5d8eea}
.stApp{background:radial-gradient(circle at 10% 0%,rgba(246,225,210,.40),transparent 24%),radial-gradient(circle at 88% 0%,rgba(217,229,255,.48),transparent 26%),linear-gradient(180deg,#fcfcfd,#f7f7fb);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}[data-testid="stSidebar"]{background:rgba(255,255,255,.94);border-right:1px solid var(--line);box-shadow:6px 0 26px rgba(55,48,100,.04)}[data-testid="stSidebar"]>div:first-child{padding:20px 14px}
.outreach-brand{height:58px;display:flex;align-items:center;gap:11px;padding:0 12px;margin:0 0 22px;border-bottom:1px solid #f0eef5}.outreach-logo{width:36px;height:36px;border-radius:11px;background:linear-gradient(135deg,#7867e8,#9b8cf4);display:flex;align-items:center;justify-content:center;color:#fff;font-size:19px;font-weight:850;box-shadow:0 8px 20px rgba(120,103,232,.24)}.outreach-name{font-size:20px;font-weight:820;letter-spacing:-.035em;color:#222238}.nav-label{font-size:11px;text-transform:uppercase;letter-spacing:.10em;color:#a0a0af;font-weight:750;padding:0 10px 8px}
.page-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin:4px 0 24px}.page-title{font-size:34px;line-height:1.05;font-weight:850;letter-spacing:-.05em;color:#202033}.page-subtitle{font-size:14px;color:var(--muted);margin-top:7px}.ist-pill{white-space:nowrap;background:#fff;border:1px solid var(--line);border-radius:999px;padding:8px 12px;color:#6d6e7e;font-size:12px;box-shadow:0 6px 18px rgba(60,55,100,.05)}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:7px;box-shadow:0 0 0 4px rgba(46,175,134,.12)}
.metric{background:rgba(255,255,255,.96);border:1px solid var(--line);border-radius:19px;padding:19px 20px;min-height:112px;box-shadow:0 8px 24px rgba(55,48,100,.045);position:relative;overflow:hidden}.metric:after{content:"";position:absolute;right:-30px;top:-30px;width:90px;height:90px;border-radius:50%;background:linear-gradient(135deg,rgba(120,103,232,.13),transparent)}.metric-label{font-size:12px;color:#77788a;font-weight:750}.metric-value{font-size:31px;font-weight:850;letter-spacing:-.05em;margin-top:8px}.metric-note{font-size:11px;color:#999aaa;margin-top:3px}.card{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 8px 28px rgba(55,48,100,.045)}.hero{background:linear-gradient(135deg,rgba(120,103,232,.12),rgba(91,141,239,.07) 58%,rgba(255,255,255,.92));border:1px solid #e5e1f7;border-radius:21px;padding:20px;box-shadow:0 14px 35px rgba(75,65,140,.07)}.section-title{font-size:16px;font-weight:800;margin:25px 0 10px}.section-sub{font-size:12px;color:#8b8c9d;margin:-4px 0 10px}.badge{display:inline-flex;padding:5px 9px;border-radius:999px;background:#eeeafd;color:#6552df;font-size:11px;font-weight:750}.status-delivered{color:#15976c;font-weight:750}.status-bounced{color:#df5365;font-weight:750}.status-replied{color:#7059d8;font-weight:750}.quick{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 7px 22px rgba(55,48,100,.04)}.small{font-size:12px;color:#858697}.stButton>button{border-radius:12px;min-height:42px;font-weight:750}.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{border-radius:12px!important;border-color:#e3e1eb!important}button[kind="primary"]{background:linear-gradient(135deg,#7867e8,#8d7df0)!important;border-color:#7867e8!important;box-shadow:0 8px 18px rgba(120,103,232,.20)}[data-testid="stTabs"] button{font-weight:750;color:#7d7e8e}[data-testid="stTabs"] button[aria-selected="true"]{color:#6552df}
</style>""",unsafe_allow_html=True)

if SENDER_EMAIL and APP_PASSWORD:
    try: sender.send_due_scheduled(SENDER_EMAIL,APP_PASSWORD)
    except Exception: pass

with st.sidebar:
    st.markdown('<div class="outreach-brand"><div class="outreach-logo">O</div><div class="outreach-name">Outreach</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="nav-label">Workspace</div>',unsafe_allow_html=True)
    page=st.radio("Navigation",["Dashboard","Emails","Customers"],label_visibility="collapsed")
    st.divider();st.markdown('<div class="small">Sending from</div>',unsafe_allow_html=True);st.caption(SENDER_EMAIL or "Not configured");st.markdown('<div class="small">Timezone</div>',unsafe_allow_html=True);st.caption("India Standard Time (IST)")


def live_clock():
    components.html("""
    <div style="font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#fff;border:1px solid #e9e7f0;border-radius:999px;padding:8px 12px;color:#6d6e7e;font-size:12px;white-space:nowrap;box-shadow:0 6px 18px rgba(60,55,100,.05);display:inline-flex;align-items:center;gap:7px;">
      <span style="width:7px;height:7px;border-radius:50%;background:#2eaf86;box-shadow:0 0 0 4px rgba(46,175,134,.12);display:inline-block;"></span>
      <span>IST · </span><span id="clock"></span>
    </div>
    <script>
      function tick(){
        const now=new Date();
        const text=new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}).format(now);
        document.getElementById('clock').textContent=text;
      }
      tick();
      setInterval(tick,1000);
    </script>
    """,height=44,scrolling=False)


def page_head(title,subtitle):
    left,right=st.columns([5,2],vertical_alignment="top")
    with left:
        st.markdown(f'<div class="page-head" style="margin-bottom:0"><div><div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div></div></div>',unsafe_allow_html=True)
    with right:
        live_clock()
    st.write("")


def relative_time(value):
    try:
        dt=pd.to_datetime(value,utc=True).to_pydatetime();sec=max(0,int((datetime.now(timezone.utc)-dt).total_seconds()))
        if sec<60:return "just now"
        mins=sec//60
        if mins<60:return f"{mins}m ago"
        hours=mins//60
        if hours<24:return f"{hours}h ago"
        days=hours//24
        if days<7:return f"{days}d ago"
        return dt.astimezone(IST).strftime("%d %b %Y")
    except Exception:return ""

def history_df():
    try:
        conn=db.get_conn();cur=conn.cursor();cur.execute("""SELECT e.id,e.contact_id,e.event_type,e.detail,e.subject,e.timestamp,c.name,c.email,c.company,c.sector FROM events e JOIN contacts c ON c.id=e.contact_id WHERE e.event_type IN ('sent','bounced','replied') ORDER BY e.timestamp DESC""");rows=[dict(r) for r in cur.fetchall()];cur.close();conn.close();return pd.DataFrame(rows)
    except Exception:return pd.DataFrame()

def send_one(contact,subject,body):
    if not SENDER_EMAIL or not APP_PASSWORD:st.error("Configure SENDER_EMAIL and SENDER_APP_PASSWORD in Streamlit Secrets.");return False
    try:sender.send_one(SENDER_EMAIL,APP_PASSWORD,contact["email"],subject,body);db.log_event(contact["id"],"sent",subject=subject);return True
    except Exception as exc:db.log_event(contact["id"],"bounced",str(exc),subject);return False

def activity_chart(metrics_df,days):
    if metrics_df.empty:return None
    raw=metrics_df.copy();raw["date"]=pd.to_datetime(raw["d"]).dt.normalize();end=pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None).normalize();start=end-pd.Timedelta(days=days-1);idx=pd.date_range(start,end,freq="D")
    series=raw.pivot_table(index="date",columns="event_type",values="c",aggfunc="sum",fill_value=0).reindex(idx,fill_value=0)
    for key in ["sent","bounced","replied"]:
        if key not in series.columns:series[key]=0
    chart_df=series[["sent","bounced","replied"]].rename(columns={"sent":"Sent","bounced":"Bounce","replied":"Unique replies"}).reset_index(names="Date");long=chart_df.melt("Date",var_name="Status",value_name="Emails");hover=alt.selection_point(on="pointerover",nearest=True,fields=["Date"],empty=False)
    base=alt.Chart(long).encode(x=alt.X("Date:T",title=None,axis=alt.Axis(format="%d %b",tickCount=min(9,days),grid=False,labelColor="#8a8b9b")),y=alt.Y("Emails:Q",title=None,scale=alt.Scale(zero=True,nice=True),axis=alt.Axis(gridColor="#efedf4",domain=False,labelColor="#8a8b9b")),color=alt.Color("Status:N",title=None,scale=alt.Scale(domain=["Sent","Bounce","Unique replies"],range=["#7b68e8","#ef6b7a","#5d8eea"])),tooltip=[alt.Tooltip("Date:T",title="Date",format="%d %b %Y"),alt.Tooltip("Status:N",title="Type"),alt.Tooltip("Emails:Q",title="Count")])
    return (base.mark_line(interpolate="monotone",strokeWidth=2.8)+base.mark_circle(size=62).encode(opacity=alt.condition(hover,alt.value(1),alt.value(.35)))+alt.Chart(long).mark_rule(color="#c9c6d6").encode(x="Date:T",opacity=alt.condition(hover,alt.value(.7),alt.value(0))).add_params(hover)).properties(height=335).configure_view(stroke=None).configure_legend(orient="top",labelColor="#676878")

if page=="Dashboard":
    page_head("Dashboard","A focused view of your outbound email performance.");metrics=db.get_metrics();a,b,c=st.columns(3)
    with a:st.markdown(f'<div class="metric"><div class="metric-label">Mail sent</div><div class="metric-value">{metrics["sent"]:,}</div><div class="metric-note">Successful outbound emails</div></div>',unsafe_allow_html=True)
    with b:st.markdown(f'<div class="metric"><div class="metric-label">Bounce</div><div class="metric-value">{metrics["bounced"]:,}</div><div class="metric-note">Delivery failures</div></div>',unsafe_allow_html=True)
    with c:st.markdown(f'<div class="metric"><div class="metric-label">Unique replies</div><div class="metric-value">{metrics["replied"]:,}</div><div class="metric-note">Customers who replied</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Email activity</div><div class="section-sub">Replies are counted by unique customer, not by number of reply messages.</div>',unsafe_allow_html=True);left,right=st.columns([4,1])
    with right:range_label=st.selectbox("Time range",["7 days","30 days","90 days"],index=1)
    if metrics["daily"]:
        with left:st.markdown('<div class="hero">',unsafe_allow_html=True);st.altair_chart(activity_chart(pd.DataFrame(metrics["daily"]),int(range_label.split()[0])),use_container_width=True);st.markdown('</div>',unsafe_allow_html=True)
    else:
        with left:st.markdown('<div class="hero"><b>Email activity will appear here</b><div class="small">Send your first email to start building the timeline.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-title">Quick actions</div>',unsafe_allow_html=True);q1,q2,q3=st.columns(3)
    with q1:st.markdown('<div class="quick"><b>✉ Write an email</b><div class="small">Compose a personal message.</div></div>',unsafe_allow_html=True)
    with q2:st.markdown('<div class="quick"><b>⇢ Send to many</b><div class="small">Launch a CSV campaign.</div></div>',unsafe_allow_html=True)
    with q3:st.markdown('<div class="quick"><b>＋ Add customer</b><div class="small">Create a customer manually.</div></div>',unsafe_allow_html=True)

elif page=="Emails":
    page_head("Emails","Send, schedule and review every outbound email.");history_tab,compose_tab,bulk_tab=st.tabs(["History","Compose","Send to many"])
    with history_tab:
        h=history_df();f1,f2,f3,f4=st.columns([2.4,1,1,.5])
        with f1:search=st.text_input("Search",placeholder="Search recipient, company or sector",label_visibility="collapsed")
        with f2:period=st.selectbox("Period",["Last 15 days","Last 30 days","All time"],label_visibility="collapsed")
        with f3:status=st.selectbox("Status",["All","Delivered","Bounced","Replied"],label_visibility="collapsed")
        with f4:st.download_button("↓",h.to_csv(index=False).encode() if not h.empty else b"","outreach-email-history.csv","text/csv",disabled=h.empty,help="Download email history")
        f=h.copy()
        if not f.empty:
            f["dt"]=pd.to_datetime(f["timestamp"],utc=True,errors="coerce")
            if period!="All time":f=f[f["dt"]>=datetime.now(timezone.utc)-timedelta(days=15 if period=="Last 15 days" else 30)]
            if status!="All":f=f[f["event_type"]==("sent" if status=="Delivered" else status.lower())]
            if search:
                mask=pd.Series(False,index=f.index)
                for field in ["email","name","company","sector","detail"]:mask|=f[field].fillna("").astype(str).str.contains(search,case=False,na=False)
                f=f[mask]
        st.markdown('<div class="card">',unsafe_allow_html=True)
        if f.empty:st.info("No outbound email history yet.")
        else:
            cols=st.columns([2.4,1,2.1,1.25]);cols[0].markdown("**TO**");cols[1].markdown("**STATUS**");cols[2].markdown("**SECTOR**");cols[3].markdown("**SENT**")
            for _,r in f.sort_values("dt",ascending=False).iterrows():
                cols=st.columns([2.4,1,2.1,1.25]);event=str(r["event_type"]);label="Delivered" if event=="sent" else event.capitalize();css="delivered" if event=="sent" else event;cols[0].write(r.get("email","") or "—");cols[1].markdown(f'<span class="status-{css}">{label}</span>',unsafe_allow_html=True);cols[2].markdown(f'<span class="badge">{r.get("sector") or "General"}</span>',unsafe_allow_html=True);cols[3].write(relative_time(r.get("timestamp")))
        st.markdown('</div>',unsafe_allow_html=True)
        if st.button("Sync replies & bounces"):
            if SENDER_EMAIL and APP_PASSWORD:result=sender.check_replies_and_bounces(SENDER_EMAIL,APP_PASSWORD);st.success(f"Synced {result['replies_found']} replies and {result['bounces_found']} bounces.");st.rerun()
            else:st.warning("Configure sender credentials first.")
    with compose_tab:
        contacts={f"{c['name']} · {c['email']}":c for c in db.get_contacts()}
        if not contacts:st.info("Add a customer from Customers first.")
        else:
            selected=st.selectbox("Customer",list(contacts.keys()));contact=contacts[selected];st.markdown(f'<span class="badge">{contact.get("sector") or "General"}</span>',unsafe_allow_html=True);mode=st.radio("Message",["Write manually","Use classified template"],horizontal=True)
            if mode=="Write manually":subject=st.text_input("Subject",placeholder="Write your subject");body=st.text_area("Message",height=240,placeholder="Write your email...")
            else:subject,body=templates.render(contact);st.text_input("Subject",subject,disabled=True);st.text_area("Message",body,height=240,disabled=True);st.caption(f"Using {contact.get('sector') or 'general'} sector template.")
            x,y=st.columns(2)
            with x:
                if st.button("Send now",type="primary",use_container_width=True):
                    if not subject.strip() or not body.strip():st.warning("Add a subject and message first.")
                    elif send_one(contact,subject,body):st.success(f"Sent to {contact['email']}.");st.rerun()
            with y:
                if st.button("Schedule for later",use_container_width=True):st.session_state["schedule_open"]=True
            if st.session_state.get("schedule_open"):
                st.markdown('<div class="card">',unsafe_allow_html=True);st.markdown("**Schedule in India Standard Time**");d=st.date_input("Date",datetime.now(IST).date(),min_value=datetime.now(IST).date());t=st.time_input("Time (IST)",(datetime.now(IST)+timedelta(hours=1)).replace(second=0,microsecond=0).time())
                if st.button("Confirm schedule",type="primary"):local=datetime.combine(d,t).replace(tzinfo=IST);db.schedule_email(contact["id"],subject,body,local.astimezone(timezone.utc).isoformat());st.session_state["schedule_open"]=False;st.success(f"Scheduled for {local.strftime('%d %b %Y · %I:%M %p')} IST.");st.rerun()
                st.markdown('</div>',unsafe_allow_html=True)
    with bulk_tab:
        st.markdown('<div class="hero"><h3 style="margin-top:0">Send many emails in one shot</h3><div class="small">Upload → classify → edit → select audience → write → send.</div></div>',unsafe_allow_html=True);uploaded=st.file_uploader("Upload CSV or Excel",type=["csv","xlsx","xls"],key="bulk_upload")
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
                s,b=templates.render(selected[0]);subject=st.text_input("Campaign subject",s,key="bulk_subject");body=st.text_area("Campaign message",b,height=210,key="bulk_body");delay=st.slider("Delay between emails (seconds)",5,60,15,5)
                if st.button(f"Send to {len(selected)} customers",type="primary",use_container_width=True):
                    if not SENDER_EMAIL or not APP_PASSWORD:st.error("Configure sender credentials first.")
                    else:
                        all_contacts={c["email"].lower():c for c in db.get_contacts()};prepared=[]
                        for row in selected:
                            email=str(row.get("email") or "").strip().lower()
                            if not email:continue
                            if email not in all_contacts:db.upsert_contacts([row]);all_contacts={c["email"].lower():c for c in db.get_contacts()}
                            if email in all_contacts:prepared.append(all_contacts[email])
                        progress=st.progress(0);box=st.empty();sent_count=failed=0
                        for i,contact in enumerate(prepared,1):
                            box.info(f"Sending {i}/{len(prepared)} · {contact['email']}");sent_count+=1 if send_one(contact,subject,body) else 0;failed+=0 if sent_count else 1;progress.progress(i/len(prepared))
                            if i<len(prepared):time.sleep(delay)
                        box.success(f"Campaign complete · {sent_count} sent · {failed} failed")
else:
    page_head("Customers","Manage customers, sectors and their complete communication history.");add_tab,list_tab=st.tabs(["Add customer","Customer list"])
    with add_tab:
        st.markdown('<div class="card">',unsafe_allow_html=True);st.markdown("### Add a customer");a,b=st.columns(2)
        with a:name=st.text_input("Name")
        with b:email=st.text_input("Email")
        a,b=st.columns(2)
        with a:company=st.text_input("Company")
        with b:sector=st.selectbox("Sector",["general","healthcare","fintech","saas_tech","manufacturing","retail_ecom"])
        if st.button("Save customer",type="primary"):
            if not name.strip() or not email.strip() or not company.strip():st.warning("Name, email and company are required.")
            else:inserted,_=db.upsert_contacts([{"name":name,"email":email,"company":company,"sector":sector}]);st.success("Customer added.") if inserted else st.info("Customer already exists or email is invalid.")
        st.markdown('</div>',unsafe_allow_html=True);st.markdown('<div class="section-title">Import customers</div>',unsafe_allow_html=True);uploaded=st.file_uploader("CSV or Excel · required: name, email, company · optional: sector",type=["csv","xlsx","xls"],key="customer_upload")
        if uploaded:
            df=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded);df.columns=[str(c).strip().lower() for c in df.columns];missing=[x for x in ["name","email","company"] if x not in df.columns]
            if missing:st.error("Missing required columns: "+", ".join(missing))
            else:
                if "sector" not in df.columns:df["sector"]=df["company"].apply(classifier.classify)
                else:df["sector"]=df.apply(lambda r:r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]),axis=1)
                edited=st.data_editor(df,num_rows="dynamic",use_container_width=True,key="customer_editor")
                if st.button("Import customers",type="primary"):inserted,skipped=db.upsert_contacts(edited.to_dict("records"));st.success(f"Imported {inserted} customers · skipped {skipped} duplicates/invalid rows.")
    with list_tab:
        customers=db.get_contacts()
        if not customers:st.info("No customers yet.")
        else:
            search=st.text_input("Search customers",placeholder="Search name, email, company or sector");filtered=[c for c in customers if not search or search.lower() in f"{c.get('name','')} {c.get('email','')} {c.get('company','')} {c.get('sector','')}".lower()]
            all_hist=pd.DataFrame(db.get_customer_history());all_csv=all_hist.to_csv(index=False).encode("utf-8") if not all_hist.empty else b"";dl1,dl2=st.columns([4,1])
            with dl1:st.markdown(f'<div class="section-title" style="margin-top:8px">{len(filtered)} customer(s)</div>',unsafe_allow_html=True)
            with dl2:st.download_button("Download all history",all_csv,"outreach-customer-history.csv","text/csv",disabled=not bool(all_csv),use_container_width=True)
            for c in filtered:
                st.markdown('<div class="card" style="margin-bottom:11px">',unsafe_allow_html=True);left,right=st.columns([3.8,1.2])
                with left:st.markdown(f"<b>{c.get('name','')}</b> <span class='badge'>{c.get('sector') or 'General'}</span>",unsafe_allow_html=True);st.markdown(f"<span class='small'>{c.get('email','')} · {c.get('company','')}</span>",unsafe_allow_html=True)
                with right:
                    customer_history=pd.DataFrame(db.get_customer_history(c["id"]));customer_csv=customer_history.to_csv(index=False).encode("utf-8") if not customer_history.empty else b"";st.download_button("Download history",customer_csv,f"{c.get('name','customer')}-history.csv","text/csv",disabled=not bool(customer_csv),use_container_width=True,key=f"customer_history_{c['id']}")
                with st.expander("View customer history",expanded=False):
                    if customer_history.empty:st.caption("No communication history yet.")
                    else:
                        display=customer_history[[x for x in ["event_type","sector","subject","detail","timestamp"] if x in customer_history.columns]].copy();display["timestamp"]=pd.to_datetime(display["timestamp"],utc=True,errors="coerce").dt.tz_convert("Asia/Kolkata").dt.strftime("%d %b %Y · %I:%M %p IST");display=display.rename(columns={"event_type":"Status","sector":"Sector","subject":"Subject","detail":"Details","timestamp":"Time"});st.dataframe(display,use_container_width=True,hide_index=True)
                st.markdown('</div>',unsafe_allow_html=True)
