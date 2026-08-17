"""Notification service for email, SMS, and push notifications"""
import os
from datetime import datetime
from config.config import Config

class NotificationService:
    """Service for sending notifications via email, SMS, and push"""
    
    def __init__(self):
        self.config = Config()
        self.email_enabled = self.config.ALERT_EMAIL_ENABLED
        self.sms_enabled = self.config.ALERT_SMS_ENABLED
        self.push_enabled = self.config.ALERT_PUSH_ENABLED
        
        # Initialize email client
        if self.email_enabled and self.config.SENDGRID_API_KEY:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                self.sendgrid_client = SendGridAPIClient(self.config.SENDGRID_API_KEY)
                self.Mail = Mail
                print("SendGrid email service initialized")
            except ImportError:
                print("Warning: SendGrid not available. Email notifications disabled.")
                self.email_enabled = False
            except Exception as e:
                print(f"Warning: SendGrid initialization failed: {e}")
                self.email_enabled = False
        
        # Initialize SMS client
        if self.sms_enabled and self.config.TWILIO_ACCOUNT_SID:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    self.config.TWILIO_ACCOUNT_SID,
                    self.config.TWILIO_AUTH_TOKEN
                )
                print("Twilio SMS service initialized")
            except ImportError:
                print("Warning: Twilio not available. SMS notifications disabled.")
                self.sms_enabled = False
            except Exception as e:
                print(f"Warning: Twilio initialization failed: {e}")
                self.sms_enabled = False
    
    def send_alert_email(self, to_email, subject, alert_data):
        """Send alert notification via email"""
        if not self.email_enabled:
            return False, "Email service not enabled"
        
        try:
            # Create email content
            html_content = self._create_alert_email_html(alert_data)
            
            message = self.Mail(
                from_email=self.config.FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True, "Email sent successfully"
            else:
                return False, f"Email sending failed: {response.status_code}"
                
        except Exception as e:
            return False, f"Email error: {str(e)}"
    
    def send_alert_sms(self, to_phone, message):
        """Send alert notification via SMS"""
        if not self.sms_enabled:
            return False, "SMS service not enabled"
        
        try:
            sms = self.twilio_client.messages.create(
                body=message,
                from_=self.config.TWILIO_PHONE_NUMBER,
                to=to_phone
            )
            
            if sms.sid:
                return True, "SMS sent successfully"
            else:
                return False, "SMS sending failed"
                
        except Exception as e:
            return False, f"SMS error: {str(e)}"
    
    def send_push_notification(self, user_id, notification_data):
        """Send push notification (placeholder for future implementation)"""
        if not self.push_enabled:
            return False, "Push notification service not enabled"
        
        # TODO: Implement push notifications using Firebase Cloud Messaging or similar
        # For now, return success for demo purposes
        return True, "Push notification queued"
    
    def notify_alert(self, alert, recipients):
        """Send alert to multiple recipients via all enabled channels"""
        results = {
            'email': [],
            'sms': [],
            'push': []
        }
        
        subject = f"🚨 {alert['severity'].upper()} Alert - {alert['message']}"
        
        for recipient in recipients:
            # Send email
            if recipient.get('email') and self.email_enabled:
                success, message = self.send_alert_email(
                    recipient['email'],
                    subject,
                    alert
                )
                results['email'].append({
                    'recipient': recipient['email'],
                    'success': success,
                    'message': message
                })
            
            # Send SMS
            if recipient.get('phone') and self.sms_enabled:
                sms_message = self._create_alert_sms(alert)
                success, message = self.send_alert_sms(
                    recipient['phone'],
                    sms_message
                )
                results['sms'].append({
                    'recipient': recipient['phone'],
                    'success': success,
                    'message': message
                })
            
            # Send push notification
            if recipient.get('user_id') and self.push_enabled:
                success, message = self.send_push_notification(
                    recipient['user_id'],
                    alert
                )
                results['push'].append({
                    'recipient': recipient['user_id'],
                    'success': success,
                    'message': message
                })
        
        return results
    
    def send_report_email(self, to_email, report_data, attachments=None):
        """Send report via email"""
        if not self.email_enabled:
            return False, "Email service not enabled"
        
        try:
            subject = f"AquaPulse Report - {report_data['title']}"
            html_content = self._create_report_email_html(report_data)
            
            message = self.Mail(
                from_email=self.config.FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # TODO: Add attachments if provided
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True, "Report email sent successfully"
            else:
                return False, f"Report email failed: {response.status_code}"
                
        except Exception as e:
            return False, f"Report email error: {str(e)}"
    
    def _create_alert_email_html(self, alert_data):
        """Create HTML content for alert email"""
        severity_colors = {
            'low': '#4CAF50',
            'medium': '#FFC107',
            'high': '#FF9800',
            'critical': '#F44336'
        }
        
        color = severity_colors.get(alert_data.get('severity', 'medium'), '#4CAF50')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {color}; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .footer {{ background: #333; color: white; padding: 10px; text-align: center; font-size: 12px; border-radius: 0 0 5px 5px; }}
                .parameter {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid {color}; }}
                .button {{ display: inline-block; padding: 10px 20px; background: {color}; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌊 AquaPulse Water Quality Alert</h1>
                    <h2>{alert_data.get('severity', 'MEDIUM').upper()} SEVERITY</h2>
                </div>
                <div class="content">
                    <h3>{alert_data.get('message', 'Water Quality Alert')}</h3>
                    <p><strong>Time:</strong> {alert_data.get('timestamp', datetime.now().isoformat())}</p>
                    <p><strong>Type:</strong> {alert_data.get('alert_type', 'General')}</p>
                    <p><strong>Description:</strong> {alert_data.get('description', 'Water quality parameters out of safe range.')}</p>
                    
                    <h4>Affected Parameters:</h4>
                    {self._format_parameters(alert_data.get('parameters', {}))}
                    
                    <p style="margin-top: 20px;">
                        <a href="{self.config.APP_URL}/alerts" class="button">View Alert Details</a>
                    </p>
                </div>
                <div class="footer">
                    <p>AquaPulse - AI-Powered Water Quality Monitoring</p>
                    <p>This is an automated alert. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _format_parameters(self, parameters):
        """Format parameters for email display"""
        if not parameters:
            return "<p>No parameter data available</p>"
        
        html = ""
        for param, value in parameters.items():
            html += f'<div class="parameter"><strong>{param}:</strong> {value}</div>'
        
        return html
    
    def _create_alert_sms(self, alert_data):
        """Create SMS message for alert"""
        message = f"AquaPulse Alert [{alert_data.get('severity', 'MEDIUM').upper()}]: {alert_data.get('message', 'Water quality issue detected')}. "
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
        message += f"Check {self.config.APP_URL}/alerts for details."
        
        return message[:160]  # SMS character limit
    
    def _create_report_email_html(self, report_data):
        """Create HTML content for report email"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
                .footer {{ background: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌊 AquaPulse Report</h1>
                    <h2>{report_data.get('title', 'Water Quality Report')}</h2>
                </div>
                <div class="content">
                    <p><strong>Report ID:</strong> {report_data.get('report_id', 'N/A')}</p>
                    <p><strong>Generated:</strong> {report_data.get('generated_at', datetime.now().isoformat())}</p>
                    <p><strong>Period:</strong> {report_data.get('start_date', '')} to {report_data.get('end_date', '')}</p>
                    <p><strong>Compliance Score:</strong> {report_data.get('compliance_score', 'N/A')}%</p>
                    
                    <p style="margin-top: 20px;">
                        The complete report is attached or available at: <a href="{self.config.APP_URL}/reports">{self.config.APP_URL}/reports</a>
                    </p>
                </div>
                <div class="footer">
                    <p>AquaPulse - AI-Powered Water Quality Monitoring</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

# Singleton instance
notification_service = NotificationService()
