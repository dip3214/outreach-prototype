# Outreach prototype

Upload a CSV/Excel contact sheet, review sector classification, send a
throttled batch through your own mailbox, and watch a live dashboard --
all running locally, all data staying in `outreach.db` on your machine.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a Gmail app password (not your normal password):
   - Turn on 2-Step Verification on your Google account if it isn't already.
   - Go to https://myaccount.google.com/apppasswords
   - Generate a password for "Mail", copy the 16-character code.

3. Set your credentials as environment variables (or copy `.env.example`
   to `.env` and load it with `python-dotenv` if you'd rather not export
   them each session):
   ```
   export SENDER_EMAIL="youraddress@gmail.com"
   export SENDER_APP_PASSWORD="your16charapppassword"
   ```

4. Run the app:
   ```
   streamlit run app.py
   ```
   Opens at http://localhost:8501

## Using it

1. **Upload contacts** -- drop your sheet in. Needs `name`, `email`,
   `company` columns at minimum. Sector is auto-classified locally from
   the company name (edit `classifier.py`'s keyword lists to tune it),
   or supply your own `sector` column. Review and edit the table before
   saving.

2. **Compose & send** -- preview the merged email for a sample contact,
   send a test to yourself first, then start a batch. Keep the first
   real run to 20-30 contacts and a daily cap well under 100 -- Gmail's
   own limits and basic sender reputation both depend on this.

3. **Dashboard** -- total sent, bounced, replied, and a daily chart.
   Click "check for replies & bounces" to poll your inbox via IMAP and
   update statuses -- run this manually for now, or put it on a
   scheduler (cron / Task Scheduler) later.

## Moving to your domain later

Nothing in the app logic changes. Once you have a domain mailbox
(e.g. on Zoho Mail with SPF/DKIM/DMARC set up), just update the
environment variables:

```
export SENDER_EMAIL="you@yourdomain.com"
export SENDER_APP_PASSWORD="your-domain-mailbox-app-password"
export SMTP_HOST="smtp.zoho.com"
export IMAP_HOST="imap.zoho.com"
```

## Notes

- All data lives in `outreach.db` (SQLite) next to these files. Back it
  up before any large batch send.
- Sector classification and template rendering run fully offline -- no
  contact data is sent to any external API to build or personalize the
  emails.
- This is a prototype for testing the flow end-to-end on a small list.
  Before scaling to your full 2,000 contacts, revisit sending limits,
  domain warm-up, and list verification.
