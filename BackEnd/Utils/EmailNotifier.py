import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from BackEnd.PostgreSQL.StationDbObject import StationDbObject, StationState


class EmailNotifier:
    """Handles email notifications for station state changes."""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.recipient_emails = os.getenv("RECIPIENT_EMAILS", "").split(",")
    
    def is_configured(self) -> bool:
        """Check if email settings are properly configured."""
        return bool(
            self.sender_email 
            and self.sender_password 
            and self.recipient_emails 
            and self.recipient_emails[0]
        )

    def send_station_state_change_email(self, station: "StationDbObject") -> bool:
        """
        Send an email notification when a station's state changes.
        Infers the old state from the new state (only 2 possible states).
        
        Args:
            station: The station object with the new state
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            print("Email not configured. Skipping notification.")
            return False

        subject, body = self._create_state_change_email_content(station)
        return self._send_email(subject, body)

    def _create_state_change_email_content(self, station: "StationDbObject") -> tuple[str, str]:
        """Create email subject and body for station state change."""
        
        new_state = station.State.value
        # Infer old state: only 2 states, so if new is Online, old was Offline and vice versa
        old_state = "Offline" if new_state == "Online" else "Online"
        
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Determine if station went online or offline
        if new_state == "Online":
            status_emoji = "🟢"
            status_message = "is now ONLINE"
        else:
            status_emoji = "🔴"
            status_message = "is now OFFLINE"
        
        subject = f"{status_emoji} Station Alert: {station.Name or station.Id} {status_message}"
        
        body = f"""
            Station State Change Notification (Station is {new_state})
            ==========================================================

            Station Information:
            --------------------
            - Station Name: {station.Name or 'N/A'}
            - Location: {station.Location or 'N/A'}
            - Manufacturer: {station.Manufacturer or 'N/A'}

            Additional Details:
            -------------------
            - Last Data Point: {station.LastDataPointTime.strftime('%Y-%m-%d %H:%M:%S UTC') if station.LastDataPointTime else 'N/A'}
            - Coordinates: {f'{station.Latitude}, {station.Longitude}' if station.Latitude and station.Longitude else 'N/A'}

            
            This Station is {new_state}
            Change Detected: {timestamp}
            

            ---
            This is an automated message from the Environmental Stations Monitoring System.
        """
        return subject, body

    def _send_email(self, subject: str, body: str) -> bool:
        """Send an email with the given subject and body."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipient_emails)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)  # type: ignore
                server.sendmail(
                    self.sender_email,  # type: ignore
                    self.recipient_emails, 
                    msg.as_string()
                )
            
            print(f"Email sent successfully: {subject}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

