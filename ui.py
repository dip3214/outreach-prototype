"""Outreach polished SaaS UI.

The UI is kept in a separate module so app.py stays a tiny Streamlit entrypoint.
"""

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


def _load_secrets() -> None:
    try:
        for key, value in st.secrets.items():
            os.environ.setdefault(key, str(value))
    except Exception:
        pass


def _setup() -> None:
    _load_secrets()
    st.set_page_config(
        page_title="Outreach",
        page_icon="✉",
        layout="wide",
        initial_sidebar_state="expanded",
    )


_setup()

# ---------- Theme -----------------------------------------------------------
st.markdown(
    """
<style>
:root{
  --ink:#202033;
  --muted:#7c7d8e;
  --line:#e8e7ef;
  --canvas:#f5f5fa;
  --white:#ffffff;
  --purple:#765fe7;
  --purple-2:#9a87f1;
  --orange:#ff8b72;
  --teal:#45d1cf;
  --blue:#4e8df7;
  --green:#28ae83;
  --red:#e86476;
}
.stApp{
  background:
    radial-gradient(circle at 8% 0%, rgba(255,222,205,.42), transparent 22%),
    radial-gradient(circle at 84% 0%, rgba(210,226,255,.50), transparent 25%),
    linear-gradient(180deg,#fafafd 0%,#f5f5fa 100%);
  color:var(--ink);
}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{
  background:rgba(255,255,255,.90);
  border-right:1px solid var(--line);
  box-shadow:8px 0 24px rgba(44,40,83,.035);
}
[data-testid="stSidebar"]>div:first-child{padding:18px 14px}
.outreach-brand{
  display:flex;align-items:center;gap:11px;
  height:58px;padding:0 9px;margin-bottom:22px;
  border-bottom:1px solid #f0eef4;
}
.logo-mark{
  width:36px;height:36px;border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--purple),var(--purple-2));
  color:white;font-size:20px;font-weight:850;
  box-shadow:0 9px 22px rgba(118,95,231,.25);
}
.brand-name{font-size:21px;font-weight:850;letter-spacing:-.04em}
.nav-caption{font-size:10px;text-transform:uppercase;letter-spacing:.11em;color:#aaaaba;font-weight:800;padding:0 9px 8px}
.page-title{font-size:34px;font-weight:850;letter-spacing:-.05em;line-height:1.04}
.page-subtitle{font-size:14px;color:var(--muted);margin-top:7px}
.ist-pill{
  background:white;border:1px solid var(--line);border-radius:999px;
  padding:8px 12px;font-size:12px;color:#707184;box-shadow:0 6px 18px rgba(50,45,90,.05);
}
.live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:7px;box-shadow:0 0 0 4px rgba(40,174,131,.10)}
.card{
  background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:20px;
  padding:20px;box-shadow:0 10px 28px rgba(44,40,83,.045);
}
.gradient-purple{
  background:linear-gradient(145deg,#d8d1ff 0%,#a896f5 44%,#7b69e8 100%);
  color:#fff;border:0;
}
.gradient-orange{
  background:linear-gradient(145deg,#ffe1d6 0%,#ffab8d 48%,#ff836d 100%);
  color:#282538;border:0;
}
.gradient-teal{
  background:linear-gradient(145deg,#cef6ef 0%,#72e2d5 48%,#52aef2 100%);
  color:#203043;border:0;
}
.metric-card{min-height:154px;border-radius:22px;padding:22px;box-shadow:0 16px 30px rgba(48,44,87,.07);position:relative;overflow:hidden}
.metric-label{font-size:13px;font-weight:720;opacity:.78}
.metric-value{font-size:39px;font-weight:860;letter-spacing:-.055em;margin-top:28px}
.metric-note{font-size:11px;opacity:.72;margin-top:3px}
.section-title{font-size:17px;font-weight:820;margin:27px 0 9px}
.section-subtitle{font-size:12px;color:#8e8f9f;margin-top:-2px;margin-bottom:12px}
.quick-card{border:1px solid var(--line);background:#fff;border-radius:18px;padding:15px 16px;box-shadow:0 8px 22px rgba(44,40,83,.035)}
.quick-title{font-weight:790;font-size:13px}.quick-note{font-size:11px;color:#8a8b9b;margin-top:4px}
.badge{display:inline-flex;padding:5px 9px;border-radius:999px;background:#eeeafd;color:#6654d7;font-size:11px;font-weight:770}
.status-sent{color:#16936d;font-weight:760}.status-bounced{color:#d94f61;font-weight:760}.status-replied{color:#6b55d5;font-weight:760}
.stButton>button{border-radius:12px;min-height:43px;font-weight:780}
button[kind="primary"],button[data-testid="stBaseButton-primary"]{
  background:#7159e6 !important;background-color:#7159e6 !important;
  color:#fff !important;border:1px solid #654bdc !important;
  box-shadow:0 10px 20px rgba(113,89,230,.24) !important;opacity:1 !important;
}
button[kind="primary"] p,button[data-testid="stBaseButton-primary"] p{color:#fff !important}
button[kind="primary"]:hover,button[data-testid="stBaseButton-primary"]:hover{background:#634bd8 !important}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{border-radius:12px!important;border-color:#e0dfea!important}
[data-testid="stTabs"] button{font-weight:760;color:#7d7e8e}
[data-testid="stTabs"] button[aria-selected="true"]{color:#6753dc}
.login-shell{max-width:1060px;margin:4vh auto 0;padding:0 10px}
.login-card{background:rgba(255,255,255,.94);border:1px solid #e8e6ef;border-radius:30px;box-shadow:0 28px 60px rgba(53,48,96,.10);overflow:hidden}
.login-left{padding:50px 48px}
.login-right{padding:42px;background:linear-gradient(145deg,#ebe7ff 0%,#c7d5ff 45%,#aceee4 100%);min-height:510px}
.login-logo{width:50px;height:50px;border-radius:16px;background:linear-gradient(135deg,#765fe7,#9a87f1);color:#fff;display:flex;align-items:center;justify-content:center;font-size:27px;font-weight:860;box-shadow:0 14px 28px rgba(118,95,231,.25)}
.login-title{font-size:36px;font-weight:860;letter-spacing:-.055em;margin:27px 0 7px}.login-copy{color:#818293;font-size:13px;line-height:1.7;margin-bottom:26px}
.feature-pill{display:flex;align-items:center;gap:10px;margin:17px 0;font-size:12px;color:#4b4b5f}
.feature-dot{width:30px;height:30px;border-radius:10px;background:rgba(255,255,255,.72);display:flex;align-items:center;justify-content:center;color:#6d57dd;font-weight:800}
.hero-label{font-size:11px;font-weight:780;letter-spacing:.08em;text-transform:uppercase;color:rgba(32,32,51,.55)}
.hero-heading{font-size:29px;font-weight:850;letter-spacing:-.05em;line-height:1.1;margin-top:10px}.hero-small{font-size:12px;color:rgba(32,32,51,.62);line-height:1.6;margin-top:10px}
.hero-stat{background:rgba(255,255,255,.55);border:1px solid rgba(255,255,255,.55);border-radius:18px;padding:16px;margin-top:30px;backdrop-filter:blur(8px)}
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Helpers ---------------------------------------------------------
def current_ist() -> datetime:
    return datetime.now(IST)


def live_clock() -> None:
    components.html(
        """
        <div style="font-family:Inter,system-ui,sans-serif;background:#fff;border:1px solid #e8e7ef;border-radius:999px;padding:8px 12px;color:#707184;font-size:12px;display:inline-flex;align-items:center;gap:7px;white-space:nowrap;box-shadow:0 6px 18px rgba(50,45,90,.05)">
          <span style="width:7px;height:7px;border-radius:50%;background:#28ae83;box-shadow:0 0 0 4px rgba(40,174,131,.10);display:inline-block"></span>
          <span>IST · </span><span id="clock"></span>
        </div>
        <script>
        function tick(){
          const text=new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}).format(new Date());
          document.getElementById('clock').textContent=text;
        }
        tick(); setInterval(tick,1000);
        </script>
        """,
        height=44,
        scrolling=False,
    )


def auth_credentials() -> tuple[str, str]:
    # Prototype fallback. Replace with Streamlit secrets for real deployment:
    # OUTREACH_LOGIN_EMAIL and OUTREACH_LOGIN_PASSWORD.
    email = os.getenv("OUTREACH_LOGIN_EMAIL", "admin@outreach.local")
    password = os.getenv("OUTREACH_LOGIN_PASSWORD", "Outreach@123")
    return email, password


def login_page() -> bool:
    if st.session_state.get("authenticated"):
        return True

    left, right = st.columns([1.05, 0.95], gap="small")
    with left:
        st.markdown('<div class="login-shell"><div class="login-card"><div class="login-left">', unsafe_allow_html=True)
        st.markdown('<div class="login-logo">O</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Welcome back.</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-copy">Sign in to your Outreach workspace and manage your customer outreach, email history and campaigns from one place.</div>', unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="you@company.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        remember = st.checkbox("Keep me signed in on this browser")
        if st.button("Sign in to Outreach", type="primary", use_container_width=True):
            expected_email, expected_password = auth_credentials()
            if email.strip().lower() == expected_email.lower() and password == expected_password:
                st.session_state["authenticated"] = True
                st.session_state["remember_me"] = remember
                st.rerun()
            else:
                st.error("Incorrect email or password.")
        st.caption("Prototype credentials are configurable with OUTREACH_LOGIN_EMAIL and OUTREACH_LOGIN_PASSWORD in Streamlit Secrets.")
        st.markdown('</div></div></div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="login-shell"><div class="login-card"><div class="login-right">', unsafe_allow_html=True)
        st.markdown('<div class="hero-label">Outbound workspace</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-heading">Reach the right customers, with the right message.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-small">Classify customers, personalise outreach, send campaigns and keep every interaction organised in one clean workspace.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-stat"><b style="font-size:13px">One workspace</b><div style="font-size:11px;color:#59596a;margin-top:5px">Customers · Emails · History · Campaigns</div></div>', unsafe_allow_html=True)
        for icon, text in [("✓", "Sector-aware outreach"), ("↗", "Bulk campaigns in one shot"), ("◷", "IST scheduling & history")]:
            st.markdown(f'<div class="feature-pill"><span class="feature-dot">{icon}</span><span>{text}</span></div>', unsafe_allow_html=True)
        st.markdown('</div></div></div>', unsafe_allow_html=True)

    return False


def safe_init_db() -> bool:
    try:
        db.init_db()
        return True
    except Exception:
        return False


def safe_metrics() -> dict:
    try:
        return db.get_metrics()
    except Exception:
        return {"sent": 0, "bounced": 0, "replied": 0, "daily": []}


def contacts() -> list[dict]:
    try:
        return db.get_contacts()
    except Exception:
        return []


def history_df() -> pd.DataFrame:
    try:
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.contact_id, e.event_type, e.detail, e.subject, e.timestamp,
                   c.name, c.email, c.company, c.sector
            FROM events e
            JOIN contacts c ON c.id = e.contact_id
            WHERE e.event_type IN ('sent','bounced','replied')
            ORDER BY e.timestamp DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close(); conn.close()
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def rel_time(value) -> str:
    try:
        dt = pd.to_datetime(value, utc=True).to_pydatetime()
        secs = max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
        if secs < 60: return "just now"
        mins = secs // 60
        if mins < 60: return f"{mins}m ago"
        hrs = mins // 60
        if hrs < 24: return f"{hrs}h ago"
        days = hrs // 24
        if days < 7: return f"{days}d ago"
        return dt.astimezone(IST).strftime("%d %b %Y")
    except Exception:
        return ""


def page_header(title: str, subtitle: str) -> None:
    left, right = st.columns([5, 2], vertical_alignment="top")
    with left:
        st.markdown(f'<div class="page-title">{title}</div><div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    with right:
        live_clock()


def activity_chart(daily: list[dict], days: int):
    if not daily:
        return None
    raw = pd.DataFrame(daily)
    raw["date"] = pd.to_datetime(raw["d"]).dt.normalize()
    end = pd.Timestamp(current_ist().date())
    start = end - pd.Timedelta(days=days - 1)
    idx = pd.date_range(start, end, freq="D")
    series = raw.pivot_table(index="date", columns="event_type", values="c", aggfunc="sum", fill_value=0).reindex(idx, fill_value=0)
    for key in ["sent", "bounced", "replied"]:
        if key not in series.columns:
            series[key] = 0
    data = series[["sent", "bounced", "replied"]].rename(columns={"sent":"Sent","bounced":"Bounce","replied":"Unique replies"}).reset_index(names="Date")
    long = data.melt("Date", var_name="Status", value_name="Count")
    hover = alt.selection_point(on="pointerover", nearest=True, fields=["Date"], empty=False)
    base = alt.Chart(long).encode(
        x=alt.X("Date:T", title=None, axis=alt.Axis(format="%d %b", tickCount=min(9, days), grid=False, labelColor="#8a8b9b")),
        y=alt.Y("Count:Q", title=None, scale=alt.Scale(zero=True, nice=True), axis=alt.Axis(gridColor="#edeaf3", domain=False, labelColor="#8a8b9b")),
        color=alt.Color("Status:N", title=None, scale=alt.Scale(domain=["Sent","Bounce","Unique replies"], range=["#765fe7","#e86476","#4e8df7"])),
        tooltip=[alt.Tooltip("Date:T", title="Date", format="%d %b %Y"), alt.Tooltip("Status:N", title="Type"), alt.Tooltip("Count:Q", title="Count")],
    )
    lines = base.mark_line(interpolate="monotone", strokeWidth=3)
    points = base.mark_circle(size=58).encode(opacity=alt.condition(hover, alt.value(1), alt.value(.35)))
    rule = alt.Chart(long).mark_rule(color="#c9c6d6").encode(x="Date:T", opacity=alt.condition(hover, alt.value(.75), alt.value(0))).add_params(hover)
    return (lines + points + rule).properties(height=330).configure_view(stroke=None).configure_legend(orient="top", labelColor="#676878")


def send_one_email(contact: dict, subject: str, body: str) -> bool:
    sender_email = os.getenv("SENDER_EMAIL", "")
    app_password = os.getenv("SENDER_APP_PASSWORD", "")
    if not sender_email or not app_password:
        st.error("Configure SENDER_EMAIL and SENDER_APP_PASSWORD in Streamlit Secrets.")
        return False
    try:
        sender.send_one(sender_email, app_password, contact["email"], subject, body)
        db.log_event(contact["id"], "sent", subject=subject)
        return True
    except Exception as exc:
        db.log_event(contact["id"], "bounced", str(exc), subject)
        st.error(f"Could not send: {exc}")
        return False


def dashboard() -> None:
    page_header("Good evening", "Here is your Outreach overview for today.")
    m = safe_metrics()
    a, b, c = st.columns(3)
    with a:
        st.markdown(f'<div class="metric-card gradient-purple"><div class="metric-label">Mail sent</div><div class="metric-value">{m["sent"]:,}</div><div class="metric-note">Successful outbound emails</div></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="metric-card gradient-orange"><div class="metric-label">Bounce</div><div class="metric-value">{m["bounced"]:,}</div><div class="metric-note">Delivery failures</div></div>', unsafe_allow_html=True)
    with c:
        st.markdown(f'<div class="metric-card gradient-teal"><div class="metric-label">Unique replies</div><div class="metric-value">{m["replied"]:,}</div><div class="metric-note">Customers who replied</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Email activity</div><div class="section-subtitle">Your sent, bounced and unique-reply activity over time.</div>', unsafe_allow_html=True)
    left, right = st.columns([4.4, 1])
    with right:
        range_label = st.selectbox("Range", ["7 days", "30 days", "90 days"], index=1)
    with left:
        chart = activity_chart(m.get("daily", []), int(range_label.split()[0]))
        if chart:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.altair_chart(chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><b>Your activity graph will appear here</b><div class="small">Send your first email to begin building the timeline.</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Quick actions</div>', unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    with q1: st.markdown('<div class="quick-card"><div class="quick-title">✉ Write an email</div><div class="quick-note">Personal outreach for one customer.</div></div>', unsafe_allow_html=True)
    with q2: st.markdown('<div class="quick-card"><div class="quick-title">↗ Send to many</div><div class="quick-note">Launch a classified CSV campaign.</div></div>', unsafe_allow_html=True)
    with q3: st.markdown('<div class="quick-card"><div class="quick-title">＋ Add customer</div><div class="quick-note">Create a customer manually.</div></div>', unsafe_allow_html=True)


def emails() -> None:
    page_header("Emails", "Send, schedule and review every outbound email.")
    history_tab, compose_tab, bulk_tab = st.tabs(["History", "Compose", "Send to many"])

    with history_tab:
        h = history_df()
        search, period, status, download = st.columns([2.5, 1, 1, .5])
        with search: q = st.text_input("Search", placeholder="Search name, company or sector", label_visibility="collapsed")
        with period: p = st.selectbox("Period", ["Last 15 days", "Last 30 days", "All time"], label_visibility="collapsed")
        with status: s = st.selectbox("Status", ["All", "Delivered", "Bounced", "Replied"], label_visibility="collapsed")
        with download:
            csv = h.to_csv(index=False).encode() if not h.empty else b""
            st.download_button("↓", csv, "outreach-email-history.csv", "text/csv", disabled=not bool(csv), help="Download email history")
        f = h.copy()
        if not f.empty:
            f["dt"] = pd.to_datetime(f["timestamp"], utc=True, errors="coerce")
            if p != "All time": f = f[f["dt"] >= datetime.now(timezone.utc) - timedelta(days=15 if p == "Last 15 days" else 30)]
            if s != "All": f = f[f["event_type"] == ("sent" if s == "Delivered" else s.lower())]
            if q:
                mask = pd.Series(False, index=f.index)
                for field in ["name", "company", "email", "sector"]:
                    mask |= f[field].fillna("").astype(str).str.contains(q, case=False, na=False)
                f = f[mask]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if f.empty:
            st.info("No outbound email history yet.")
        else:
            head = st.columns([.45,1.55,1.55,2.3,1.2,1])
            for col, text in zip(head, ["#", "NAME", "COMPANY", "EMAIL", "SECTOR", "SENT"]): col.markdown(f"**{text}**")
            for n, (_, row) in enumerate(f.sort_values("dt", ascending=False).iterrows(), 1):
                cols = st.columns([.45,1.55,1.55,2.3,1.2,1])
                cols[0].write(n); cols[1].write(row.get("name") or "—"); cols[2].write(row.get("company") or "—"); cols[3].write(row.get("email") or "—"); cols[4].markdown(f'<span class="badge">{row.get("sector") or "General"}</span>', unsafe_allow_html=True); cols[5].write(rel_time(row.get("timestamp")))
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Sync replies & bounces"):
            sender_email = os.getenv("SENDER_EMAIL", ""); app_password = os.getenv("SENDER_APP_PASSWORD", "")
            if sender_email and app_password:
                try:
                    result = sender.check_replies_and_bounces(sender_email, app_password)
                    st.success(f"Synced {result['replies_found']} replies and {result['bounces_found']} bounces.")
                    st.rerun()
                except Exception as exc: st.error(f"Sync failed: {exc}")
            else: st.warning("Configure sender credentials first.")

    with compose_tab:
        cs = contacts()
        options = {f"{c['name']} · {c['email']}": c for c in cs}
        if not options:
            st.info("Add a customer from Customers first.")
        else:
            chosen = st.selectbox("Customer", list(options.keys()))
            customer = options[chosen]
            st.markdown(f'<span class="badge">{customer.get("sector") or "General"}</span>', unsafe_allow_html=True)
            mode = st.radio("Message", ["Write manually", "Use classified template"], horizontal=True)
            if mode == "Write manually":
                subject = st.text_input("Subject", placeholder="Write your subject")
                body = st.text_area("Message", height=245, placeholder="Write your email...")
            else:
                subject, body = templates.render(customer)
                st.text_input("Subject", subject, disabled=True)
                st.text_area("Message", body, height=245, disabled=True)
                st.caption(f"Using {customer.get('sector') or 'general'} sector template.")
            x, y = st.columns(2)
            with x:
                if st.button("Send now", type="primary", use_container_width=True):
                    if not subject.strip() or not body.strip(): st.warning("Add a subject and message first.")
                    elif send_one_email(customer, subject, body): st.success(f"Sent to {customer['email']}"); st.rerun()
            with y:
                if st.button("Schedule for later", use_container_width=True): st.session_state["schedule_open"] = True
            if st.session_state.get("schedule_open"):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Schedule in India Standard Time**")
                d = st.date_input("Date", current_ist().date(), min_value=current_ist().date())
                t = st.time_input("Time (IST)", (current_ist() + timedelta(hours=1)).replace(second=0, microsecond=0).time())
                if st.button("Confirm schedule", type="primary"):
                    local = datetime.combine(d, t).replace(tzinfo=IST)
                    db.schedule_email(customer["id"], subject, body, local.astimezone(timezone.utc).isoformat())
                    st.session_state["schedule_open"] = False
                    st.success(f"Scheduled for {local.strftime('%d %b %Y · %I:%M %p')} IST")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    with bulk_tab:
        st.markdown('<div class="card gradient-purple"><div style="font-size:18px;font-weight:820">Send many emails in one shot</div><div style="font-size:12px;opacity:.82;margin-top:5px">Upload → classify → edit → select audience → write → send.</div></div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"], key="bulk_upload")
        if uploaded:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [str(c).strip().lower() for c in df.columns]
            missing = [x for x in ["name","email","company"] if x not in df.columns]
            if missing:
                st.error("Missing required columns: " + ", ".join(missing))
            else:
                if "sector" not in df.columns: df["sector"] = df["company"].apply(classifier.classify)
                else: df["sector"] = df.apply(lambda r: r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]), axis=1)
                edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="bulk_editor")
                st.session_state["bulk_rows"] = edited.to_dict("records")
        rows = st.session_state.get("bulk_rows", [])
        if rows:
            sectors = ["All sectors"] + sorted({str(r.get("sector") or "general") for r in rows})
            selected_sector = st.selectbox("Audience", sectors)
            selected_rows = rows if selected_sector == "All sectors" else [r for r in rows if (r.get("sector") or "general") == selected_sector]
            st.write(f"{len(selected_rows)} recipient(s) selected")
            if selected_rows:
                default_subject, default_body = templates.render(selected_rows[0])
                subject = st.text_input("Campaign subject", default_subject, key="bulk_subject")
                body = st.text_area("Campaign message", default_body, height=220, key="bulk_body")
                delay = st.slider("Delay between emails (seconds)", 5, 60, 15, 5)
                if st.button(f"Send to {len(selected_rows)} customers", type="primary", use_container_width=True):
                    all_contacts = {c["email"].lower(): c for c in contacts()}
                    prepared = []
                    for row in selected_rows:
                        email = str(row.get("email") or "").strip().lower()
                        if not email: continue
                        if email not in all_contacts:
                            db.upsert_contacts([row]); all_contacts = {c["email"].lower(): c for c in contacts()}
                        if email in all_contacts: prepared.append(all_contacts[email])
                    progress = st.progress(0); status_box = st.empty(); sent_count = failed = 0
                    for i, customer in enumerate(prepared, 1):
                        status_box.info(f"Sending {i}/{len(prepared)} · {customer['email']}")
                        ok = send_one_email(customer, subject, body)
                        sent_count += 1 if ok else 0; failed += 0 if ok else 1
                        progress.progress(i / len(prepared))
                        if i < len(prepared): time.sleep(delay)
                    status_box.success(f"Campaign complete · {sent_count} sent · {failed} failed")


def customers_page() -> None:
    page_header("Customers", "Keep your audience organised and understand every interaction.")
    add_tab, list_tab = st.tabs(["Add customer", "Customer list"])
    with add_tab:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Add a customer")
        a, b = st.columns(2)
        with a: name = st.text_input("Name")
        with b: email = st.text_input("Email")
        a, b = st.columns(2)
        with a: company = st.text_input("Company")
        with b: sector = st.selectbox("Sector", ["general","healthcare","fintech","saas_tech","manufacturing","retail_ecom"])
        if st.button("Save customer", type="primary"):
            if not name.strip() or not email.strip() or not company.strip(): st.warning("Name, email and company are required.")
            else:
                inserted, _ = db.upsert_contacts([{"name":name,"email":email,"company":company,"sector":sector}])
                st.success("Customer added.") if inserted else st.info("Customer already exists or email is invalid.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Import customers</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("CSV or Excel · required: name, email, company · optional: sector", type=["csv","xlsx","xls"], key="customer_upload")
        if uploaded:
            df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            df.columns = [str(c).strip().lower() for c in df.columns]
            missing = [x for x in ["name","email","company"] if x not in df.columns]
            if missing: st.error("Missing required columns: " + ", ".join(missing))
            else:
                if "sector" not in df.columns: df["sector"] = df["company"].apply(classifier.classify)
                else: df["sector"] = df.apply(lambda r: r["sector"] if pd.notna(r["sector"]) and str(r["sector"]).strip() else classifier.classify(r["company"]), axis=1)
                edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="customer_editor")
                if st.button("Import customers", type="primary"):
                    inserted, skipped = db.upsert_contacts(edited.to_dict("records"))
                    st.success(f"Imported {inserted} customers · skipped {skipped} duplicates/invalid rows.")
    with list_tab:
        cs = contacts()
        if not cs:
            st.info("No customers yet.")
            return
        q = st.text_input("Search customers", placeholder="Search name, email, company or sector")
        filtered = [c for c in cs if not q or q.lower() in f"{c.get('name','')} {c.get('email','')} {c.get('company','')} {c.get('sector','')}".lower()]
        all_history = pd.DataFrame(db.get_customer_history())
        all_csv = all_history.to_csv(index=False).encode() if not all_history.empty else b""
        l, r = st.columns([4,1])
        with l: st.markdown(f'<div class="section-title" style="margin-top:8px">{len(filtered)} customer(s)</div>', unsafe_allow_html=True)
        with r: st.download_button("Download all history", all_csv, "outreach-customer-history.csv", "text/csv", disabled=not bool(all_csv), use_container_width=True)
        for customer in filtered:
            st.markdown('<div class="card" style="margin-bottom:11px">', unsafe_allow_html=True)
            left, right = st.columns([3.9,1.1])
            with left:
                st.markdown(f'<b>{customer.get("name","")}</b> <span class="badge">{customer.get("sector") or "General"}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="small">{customer.get("email","")} · {customer.get("company","")}</div>', unsafe_allow_html=True)
            history = pd.DataFrame(db.get_customer_history(customer["id"]))
            csv = history.to_csv(index=False).encode() if not history.empty else b""
            with right: st.download_button("Download history", csv, f"{customer.get('name','customer')}-history.csv", "text/csv", disabled=not bool(csv), use_container_width=True, key=f"hist_{customer['id']}")
            with st.expander("View customer history"):
                if history.empty:
                    st.caption("No communication history yet.")
                else:
                    view = history[[x for x in ["event_type","sector","subject","detail","timestamp"] if x in history.columns]].copy()
                    view["timestamp"] = pd.to_datetime(view["timestamp"], utc=True, errors="coerce").dt.tz_convert("Asia/Kolkata").dt.strftime("%d %b %Y · %I:%M %p IST")
                    view = view.rename(columns={"event_type":"Status","sector":"Sector","subject":"Subject","detail":"Details","timestamp":"Time"})
                    st.dataframe(view, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    if not login_page():
        return
    if not safe_init_db():
        st.warning("Customer data is temporarily unavailable. The Outreach interface is still available.")
    with st.sidebar:
        if st.button("Log out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.rerun()
    page = st.radio("Navigation", ["Dashboard","Emails","Customers"], label_visibility="collapsed") if False else None
    # Read the navigation control already rendered by the authenticated shell.
    st.sidebar.empty()
    # Re-render compact sidebar after login.
    with st.sidebar:
        st.markdown('<div class="outreach-brand"><div class="logo-mark">O</div><div class="brand-name">Outreach</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-caption">Workspace</div>', unsafe_allow_html=True)
        selected = st.radio("Navigation", ["Dashboard","Emails","Customers"], label_visibility="collapsed", key="main_nav")
        st.divider()
        st.markdown('<div class="small">Sending from</div>', unsafe_allow_html=True)
        st.caption(os.getenv("SENDER_EMAIL", "Not configured"))
        st.markdown('<div class="small">Timezone</div>', unsafe_allow_html=True)
        st.caption("India Standard Time (IST)")
        if st.button("Log out", use_container_width=True, key="logout_button"):
            st.session_state["authenticated"] = False
            st.rerun()
    if selected == "Dashboard": dashboard()
    elif selected == "Emails": emails()
    else: customers_page()


if __name__ == "__main__":
    main()
