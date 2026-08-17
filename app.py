"""Outreach Streamlit entrypoint."""

import streamlit as st

import ui


def compact_login():
    """Render the login as a compact centered form."""
    if st.session_state.get("authenticated"):
        return True

    # Keep the page visually compact and prevent the oversized blank area
    # created by the previous raw-HTML login wrapper.
    st.markdown("""
    <style>
      .login-screen-spacer{height:6vh}
      .login-title-clean{font-size:30px;font-weight:850;letter-spacing:-.045em;line-height:1.1;margin:18px 0 7px;color:#222235}
      .login-sub-clean{font-size:13px;color:#858696;line-height:1.5;margin-bottom:20px}
      .login-logo-clean{width:52px;height:52px;border-radius:15px;background:linear-gradient(135deg,#7867e8,#9b8cf4);display:flex;align-items:center;justify-content:center;color:white;font-size:27px;font-weight:850;box-shadow:0 10px 22px rgba(120,103,232,.22)}
      .login-note-clean{font-size:11px;color:#9a9aa8;text-align:center;margin-top:12px}
      [data-testid="stForm"]{border:0!important;padding:0!important}
      .login-column{max-width:430px;margin:0 auto}
    </style>
    <div class="login-screen-spacer"></div>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1, 1.35, 1])
    with center:
        st.markdown('<div class="login-column">', unsafe_allow_html=True)
        st.markdown('<div class="login-logo-clean">O</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title-clean">Sign in to Outreach</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub-clean">Access your email outreach workspace, customers and campaign history.</div>', unsafe_allow_html=True)

        email = st.text_input("Email", placeholder="you@company.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

        if st.button("Sign in", type="primary", use_container_width=True):
            expected_email, expected_password = ui.credentials()
            if email.strip().lower() == expected_email.lower() and password == expected_password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect email or password.")

        st.markdown('<div class="login-note-clean">Secure access to your Outreach workspace</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    return False


# Replace only the login renderer. The existing dashboard, emails and
# customer workspace remain unchanged.
ui.login = compact_login
ui.main()
