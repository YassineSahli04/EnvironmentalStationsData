import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from BackEnd.PostgreSQL.StationDbObject import StationDbObject, StationState
import logging


class EmailNotifier:
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "alisahliinatserveur@gmail.com"
    sender_password = "yvlr bhyv qsuw tuhs"
    def __init__(self, recipients: list[str]):
        self.logger = logging.getLogger(__name__)
        self.recipient_emails = recipients

    def send_station_state_change_email(self, station: StationDbObject) -> None:
        subject, body = self._create_state_change_email_content(station)
        self._send_email(subject, body)
    
    def _send_email(self, subject: str, body: str) -> None:
        try:
            recipients = []
            for e in (self.recipient_emails or []):
                if isinstance(e, str):
                    e = e.strip()
                    if e:
                        recipients.append(e)

            if not recipients:
                self.logger.warning("No valid recipient emails. Email not sent. subject=%s", subject)
                return
            

            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", _charset="utf-8"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())

            self.logger.info("Email sent successfully: %s (to=%d)", subject, len(recipients))

        except Exception as e:
            self.logger.exception("Failed to send email: %s", e)


    def _create_state_change_email_content(self, station: StationDbObject) -> tuple[str, str]:       
        new_state = station.State
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if new_state == StationState.Online:
            status_emoji = "🟢"
            status_message = "is now ONLINE"
        else:
            status_emoji = "🔴"
            status_message = "is now OFFLINE"
        
        subject = f"{status_emoji} Station Alert: {station.Name or station.Id} {status_message}"
        
        body = (
        f"🔔 Station alert: {station.Name or 'Unknown'} is now {new_state.value}\n"
        f"Station\n"
        f"  • Name: {station.Name or 'N/A'}\n"
        f"  • Location: {station.Location or 'N/A'}\n"
        f"  • Manufacturer: {station.Manufacturer or 'N/A'}\n\n"
        f"Status\n"
        f"  • New state: {new_state.value}\n"
        f"  • Detected at: {timestamp}\n"
        f"  • Last data point: {station.LastDataPointTime.strftime('%Y-%m-%d %H:%M:%S UTC') if station.LastDataPointTime else 'N/A'}\n"
        f"  • Coordinates: {f'{station.Latitude}, {station.Longitude}' if station.Latitude is not None and station.Longitude is not None else 'N/A'}\n\n"
        f"--\n"
        f"Automated message • Environmental Stations Monitoring System\n"
        )

        return subject, body

    
