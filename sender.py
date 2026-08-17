"""
Sending and reply-tracking, both against your own mailbox.
Prototype defaults: Gmail SMTP + IMAP with an app password.
Swap host/port when you move to a domain mailbox later -- nothing
else in this file changes.
"""

import smtplib
import imaplib
import email
import time
import os
from email.mime.text import MIMEText

import db

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")


def send_one(sender_email, app_password, to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, [to_email], msg.as_string())


def send_batch(sender_email, app_password, contacts, render_fn, delay_seconds=60,
                daily_cap=80, progress_callback=None):
    """
    contacts: list of contact dicts (must include id, email, sector, name, company).
    render_fn: function(contact) -> (subject, body).
    Stops at daily_cap. Logs 'sent' or 'bounced' event per contact.
    """
    sent_count = 0
    for contact in contacts:
        if sent_count >= daily_cap:
            break
        subject, body = render_fn(contact)
        try:
            send_one(sender_email, app_password, contact["email"], subject, body)
            db.log_event(contact["id"], "sent")
        except smtplib.SMTPRecipientsRefused:
            db.log_event(contact["id"], "bounced", "recipient refused at send time")
        except Exception as e:
            db.log_event(contact["id"], "bounced", str(e))
        sent_count += 1
        if progress_callback:
            progress_callback(sent_count, contact["email"])
        if sent_count < daily_cap:
            time.sleep(delay_seconds)
    return sent_count


def check_replies_and_bounces(sender_email, app_password, lookback=50):
    """
    Polls your own inbox via IMAP. Matches sender addresses in recent
    messages against contact emails to mark replies. Looks for
    mailer-daemon / delivery-failure messages to mark bounces.
    """
    conn = imaplib.IMAP4_SSL(IMAP_HOST)
    conn.login(sender_email, app_password)
    conn.select("inbox")

    _, data = conn.search(None, "ALL")
    ids = data[0].split()[-lookback:]

    contacts = db.get_contacts()
    email_to_contact = {c["email"].lower(): c for c in contacts}

    replies_found, bounces_found = 0, 0
    for msg_id in ids:
        _, msg_data = conn.fetch(msg_id, "(RFC822)")
        raw = msg_data[0][1]
        parsed = email.message_from_bytes(raw)
        from_addr = email.utils.parseaddr(parsed.get("From", ""))[1].lower()

        if "mailer-daemon" in from_addr or "postmaster" in from_addr:
            body_text = _get_body_text(parsed)
            for addr, contact in email_to_contact.items():
                if addr in body_text.lower() and contact["status"] != "bounced":
                    db.log_event(contact["id"], "bounced", "detected via IMAP delivery failure")
                    bounces_found += 1
            continue

        if from_addr in email_to_contact:
            contact = email_to_contact[from_addr]
            if contact["status"] not in ("replied",):
                db.log_event(contact["id"], "replied")
                replies_found += 1

    conn.logout()
    return {"replies_found": replies_found, "bounces_found": bounces_found}


def _get_body_text(parsed_msg):
    if parsed_msg.is_multipart():
        for part in parsed_msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(errors="ignore")
                except Exception:
                    continue
        return ""
    try:
        return parsed_msg.get_payload(decode=True).decode(errors="ignore")
    except Exception:
        return ""
