import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base    import MIMEBase
from email.mime.text    import MIMEText
from email               import encoders
from datetime            import date
import pathlib
from config              import (EMAIL_SENDER, EMAIL_PASSWORD,
                                   EMAIL_TO, SMTP_HOST, SMTP_PORT)

def send_report(pdf_path: str, account_count: int):
    """Attach PDF and send to all recipients in EMAIL_TO list."""
    today = date.today().strftime("%d %b %Y")
    filename = pathlib.Path(pdf_path).name

    msg = MIMEMultipart()
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = ", ".join(EMAIL_TO)
    msg["Subject"] = f"Gemalgo Trading Report — {today}"

    body = f"""Hi,

Please find attached the Gemalgo automated trading performance report for {today}.

This report covers {account_count} active client account(s) with the following metrics:
  • Current balance & equity
  • Monthly, weekly and daily P&L
  • Win rate (overall, longs, shorts)
  • Maximum drawdown
  • Profit factor
  • Trade statistics

This report is generated automatically from the Gemalgo API.

Regards,
Gemalgo Automated Reporting System
"""
    msg.attach(MIMEText(body, "plain"))

    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition",
                    f'attachment; filename="{filename}"')
    msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_TO, msg.as_string())

    print(f"✓ Email sent to: {', '.join(EMAIL_TO)}")